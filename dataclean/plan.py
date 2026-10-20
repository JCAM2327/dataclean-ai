from __future__ import annotations

from typing import Any

import pandas as pd

HIGH_MISSING_PCT = 40.0
MIN_OBS_FOR_OUTLIERS = 8
OUTLIER_FRACTION = 0.01


def build_cleaning_plan(
    df: pd.DataFrame,
    imputation_strategies: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Build an explicit cleaning plan: column, action and justification.

    Rules:
    - drop exact duplicate rows
    - exclude constant columns and likely identifiers
    - drop columns with missing rate at or above 40%
    - impute remaining nulls according to configurable strategies
      (defaults: median for numeric, mode for categorical)
    - mark imputed nulls with a boolean indicator column
    - clip numeric columns that present IQR outliers (bounds from observed data)

    imputation_strategies keys:
      - "__numeric__": "median" | "mean" | "mode" | "constant"
      - "__categorical__": "mode" | "median" | "mean" | "constant"
      - column name: same values, or {"strategy": "...", "value": ...} for constant
    """
    plan: list[dict[str, Any]] = []
    n_rows = len(df)
    if n_rows == 0:
        return plan

    duplicate_count = int(df.duplicated().sum())
    if duplicate_count:
        plan.append({
            "column": None,
            "action": "drop_duplicates",
            "justification": (
                f"{duplicate_count} filas duplicadas exactas no aportan observaciones nuevas."
            ),
            "params": {"count": duplicate_count},
        })

    for name in df.columns:
        series = df[name]
        column = str(name)
        missing = int(series.isna().sum())
        missing_pct = 100 * missing / n_rows
        nunique = int(series.nunique(dropna=True))

        if nunique == 1 and missing < n_rows:
            plan.append({
                "column": column,
                "action": "drop_column",
                "justification": "Columna constante: no aporta varianza ni señal.",
                "params": {"reason": "constant"},
            })
            continue

        if _is_identifier(series, nunique, n_rows):
            plan.append({
                "column": column,
                "action": "drop_column",
                "justification": "Identificador: se excluye del conjunto de features.",
                "params": {"reason": "identifier"},
            })
            continue

        if missing == 0:
            pass
        elif missing_pct >= HIGH_MISSING_PCT:
            plan.append({
                "column": column,
                "action": "drop_column",
                "justification": (
                    f"Nulos en {round(missing_pct, 2)}% de las filas; imputar distorsionaría la columna."
                ),
                "params": {"reason": "high_missing", "missing_pct": round(missing_pct, 2)},
            })
            continue
        else:
            numeric = _mostly_numeric(series)
            strategy, fill_value = _resolve_imputation(
                column, numeric, series, imputation_strategies or {}
            )
            action = {
                "median": "impute_median",
                "mean": "impute_mean",
                "mode": "impute_mode",
                "constant": "impute_constant",
            }[strategy]
            justification = _imputation_justification(strategy, missing_pct, fill_value)
            plan.append({
                "column": column,
                "action": "add_missing_indicator",
                "justification": "Conserva la señal de ausencia antes de imputar.",
                "params": {"indicator": f"{column}__missing"},
            })
            plan.append({
                "column": column,
                "action": action,
                "justification": justification,
                "params": {
                    "strategy": strategy,
                    "value": fill_value,
                    "missing": missing,
                },
            })

        # Outlier clipping for numeric columns that are kept
        if _mostly_numeric(series):
            bounds = _iqr_bounds(series)
            if bounds is not None:
                lower, upper, outlier_count = bounds
                plan.append({
                    "column": column,
                    "action": "clip_outliers",
                    "justification": (
                        f"{outlier_count} observaciones fuera del rango IQR "
                        f"[{round(lower, 4)}, {round(upper, 4)}]; se recortan a los límites."
                    ),
                    "params": {
                        "lower": round(float(lower), 6),
                        "upper": round(float(upper), 6),
                        "count": outlier_count,
                    },
                })

    return plan


def apply_plan(df: pd.DataFrame, plan: list[dict[str, Any]]) -> pd.DataFrame:
    """Apply a cleaning plan and return a new dataframe."""
    out = df.copy()
    for step in plan:
        action = step["action"]
        column = step["column"]
        params = step.get("params") or {}
        if action == "drop_duplicates":
            out = out.drop_duplicates().reset_index(drop=True)
        elif action == "drop_column":
            if column in out.columns:
                out = out.drop(columns=[column])
        elif action == "add_missing_indicator":
            indicator = params.get("indicator") or f"{column}__missing"
            if column in out.columns:
                out[indicator] = out[column].isna().astype(int)
        elif action in {"impute_median", "impute_mean", "impute_mode", "impute_constant"}:
            if column in out.columns:
                value = params.get("value")
                if action == "impute_median":
                    if value is None:
                        numeric = pd.to_numeric(out[column], errors="coerce")
                        value = numeric.median()
                    out[column] = pd.to_numeric(out[column], errors="coerce").fillna(value)
                elif action == "impute_mean":
                    if value is None:
                        numeric = pd.to_numeric(out[column], errors="coerce")
                        value = numeric.mean()
                    out[column] = pd.to_numeric(out[column], errors="coerce").fillna(value)
                elif action == "impute_mode":
                    if value is None:
                        mode = out[column].mode(dropna=True)
                        value = None if mode.empty else mode.iloc[0]
                    if value is not None:
                        out[column] = out[column].fillna(value)
                elif action == "impute_constant":
                    if value is not None:
                        out[column] = out[column].fillna(value)
        elif action == "clip_outliers":
            if column in out.columns:
                lower = params.get("lower")
                upper = params.get("upper")
                if lower is not None and upper is not None:
                    numeric = pd.to_numeric(out[column], errors="coerce")
                    clipped = numeric.clip(lower=lower, upper=upper)
                    # Preserve original non-numeric as NaN already handled by to_numeric
                    out[column] = clipped.where(numeric.notna(), out[column])
        else:
            raise ValueError(f"Acción de plan no soportada: {action}")
    return out


def quality_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Summarize quality differences between two analysis summaries."""
    return {
        "rows_before": before["rows"],
        "rows_after": after["rows"],
        "rows_removed": before["rows"] - after["rows"],
        "columns_before": before["columns"],
        "columns_after": after["columns"],
        "duplicate_rows_before": before["duplicate_rows"],
        "duplicate_rows_after": after["duplicate_rows"],
        "issues_before": before["issue_count"],
        "issues_after": after["issue_count"],
        "issues_resolved": before["issue_count"] - after["issue_count"],
    }


def _resolve_imputation(
    column: str,
    numeric: bool,
    series: pd.Series,
    strategies: dict[str, Any],
) -> tuple[str, Any]:
    """Return (strategy, fill_value) for the column."""
    def _parse(spec: Any) -> tuple[str, Any]:
        if isinstance(spec, dict):
            return str(spec.get("strategy", "")).lower(), spec.get("value")
        if spec:
            return str(spec).lower(), None
        return "", None

    # Column-specific override
    strategy, value = _parse(strategies.get(column))

    if not strategy:
        type_key = "__numeric__" if numeric else "__categorical__"
        strategy, value = _parse(strategies.get(type_key))

    if not strategy:
        strategy = "median" if numeric else "mode"

    if strategy not in {"median", "mean", "mode", "constant"}:
        strategy = "median" if numeric else "mode"

    if strategy == "constant":
        fill = value if value is not None else (0 if numeric else "missing")
        return "constant", _jsonable(fill)

    observed = series.dropna()
    if strategy == "median":
        if numeric:
            num = pd.to_numeric(observed, errors="coerce")
            med = num.median()
            return "median", None if pd.isna(med) else round(float(med), 6)
        # fallback for categorical
        mode = observed.mode(dropna=True)
        return "mode", None if mode.empty else _jsonable(mode.iloc[0])
    if strategy == "mean":
        if numeric:
            num = pd.to_numeric(observed, errors="coerce")
            mean = num.mean()
            return "mean", None if pd.isna(mean) else round(float(mean), 6)
        mode = observed.mode(dropna=True)
        return "mode", None if mode.empty else _jsonable(mode.iloc[0])
    # mode
    mode = observed.mode(dropna=True)
    return "mode", None if mode.empty else _jsonable(mode.iloc[0])


def _imputation_justification(strategy: str, missing_pct: float, value: Any) -> str:
    pct = round(missing_pct, 2)
    if strategy == "median":
        return f"Nulos en {pct}%; se imputa la mediana (robusta a colas)."
    if strategy == "mean":
        return f"Nulos en {pct}%; se imputa la media."
    if strategy == "mode":
        return f"Nulos en {pct}%; se imputa la moda observada."
    return f"Nulos en {pct}%; se imputa el valor constante {value!r}."


def _mostly_numeric(series: pd.Series) -> bool:
    observed = series.dropna()
    if observed.empty:
        return pd.api.types.is_numeric_dtype(series)
    numeric = pd.to_numeric(observed, errors="coerce")
    return int(numeric.notna().sum()) >= max(1, int(0.8 * len(observed)))


def _iqr_bounds(series: pd.Series) -> tuple[float, float, int] | None:
    """Return (lower, upper, outlier_count) or None if not applicable."""
    numeric = pd.to_numeric(series, errors="coerce").dropna()
    if len(numeric) < MIN_OBS_FOR_OUTLIERS:
        return None
    q1 = float(numeric.quantile(0.25))
    q3 = float(numeric.quantile(0.75))
    iqr = q3 - q1
    if iqr <= 0:
        return None
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outliers = int(((numeric < lower) | (numeric > upper)).sum())
    if outliers == 0 or outliers / len(numeric) < OUTLIER_FRACTION:
        return None
    return lower, upper, outliers


def _is_identifier(series: pd.Series, nunique: int, n_rows: int) -> bool:
    name = str(series.name).lower()
    named_id = name in {"id", "uuid", "guid"} or name.endswith("_id")
    unique_text = nunique == n_rows and (
        pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)
    )
    return named_id or unique_text


def _jsonable(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value

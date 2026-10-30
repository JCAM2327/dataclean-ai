from __future__ import annotations

from typing import Any

import pandas as pd


def build_cleaning_plan(
    df: pd.DataFrame,
    imputation_strategies: dict[str, Any] | None = None,
    scale_numeric: bool = False,
    encode_categorical: str | None = None,
    onehot_drop_first: bool = False,
    drop_low_variance_threshold: float | None = None,
    drop_high_correlation_threshold: float | None = None,
) -> list[dict[str, Any]]:
    """Build an explicit cleaning plan with column, action, justification and optional params."""
    plan: list[dict[str, Any]] = []
    n_rows = len(df)
    strategies = imputation_strategies or {}

    # Duplicates
    if df.duplicated().any():
        plan.append({
            "column": None,
            "action": "drop_duplicates",
            "justification": "Eliminar filas duplicadas exactas que no aportan información adicional.",
        })

    # Identify columns to drop early (constant, ID, low variance)
    early_dropped: set[str] = set()
    for name in list(df.columns):
        series = df[name]
        nunique = int(series.nunique(dropna=True))
        missing = int(series.isna().sum())

        # Constant
        if nunique == 1 and missing < n_rows:
            plan.append({
                "column": str(name),
                "action": "drop_column",
                "justification": f"La columna '{name}' es constante y no aporta señal.",
                "params": {"reason": "constant"},
            })
            early_dropped.add(str(name))
            continue

        # Likely ID: unique object or named id
        if (nunique == n_rows and series.dtype == object) or str(name).lower() in {"id", "identifier"} or str(name).lower().endswith("_id"):
            plan.append({
                "column": str(name),
                "action": "drop_column",
                "justification": f"La columna '{name}' parece un identificador (único o por nombre).",
                "params": {"reason": "likely_id"},
            })
            early_dropped.add(str(name))
            continue

        # Low variance (numeric only)
        if drop_low_variance_threshold is not None and drop_low_variance_threshold > 0:
            numeric = pd.to_numeric(series, errors="coerce")
            valid = numeric.dropna()
            if len(valid) >= 2:
                std = float(valid.std(ddof=0))  # population
                if std < drop_low_variance_threshold:
                    plan.append({
                        "column": str(name),
                        "action": "drop_column",
                        "justification": f"La columna numérica '{name}' tiene baja varianza (std={std:.6f} < {drop_low_variance_threshold}).",
                        "params": {"reason": "low_variance", "std": std, "threshold": drop_low_variance_threshold},
                    })
                    early_dropped.add(str(name))
                    continue

    # High correlation (numeric only, after early drops)
    if drop_high_correlation_threshold is not None and drop_high_correlation_threshold > 0 and drop_high_correlation_threshold < 1:
        numeric_cols = []
        for name in df.columns:
            if str(name) in early_dropped:
                continue
            series = df[name]
            numeric = pd.to_numeric(series, errors="coerce")
            if pd.api.types.is_numeric_dtype(series) or (numeric.notna().mean() > 0.8 and len(numeric.dropna()) >= 2):
                numeric_cols.append(str(name))
        if len(numeric_cols) >= 2:
            num_df = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
            corr = num_df.corr(method="pearson", min_periods=2).abs()
            pairs = []
            for i, c1 in enumerate(numeric_cols):
                for c2 in numeric_cols[i + 1:]:
                    val = corr.loc[c1, c2]
                    if pd.notna(val) and val >= drop_high_correlation_threshold:
                        pairs.append((c1, c2, float(val)))
            # Sort by correlation descending to process strongest first
            pairs.sort(key=lambda x: -x[2])
            dropped_corr: set[str] = set()
            for c1, c2, corr_val in pairs:
                if c1 in dropped_corr or c2 in dropped_corr:
                    continue
                # Prefer to drop the one with higher missing rate; tie-break by lower std then name
                m1 = int(df[c1].isna().sum())
                m2 = int(df[c2].isna().sum())
                s1 = float(num_df[c1].std(ddof=0)) if len(num_df[c1].dropna()) else 0.0
                s2 = float(num_df[c2].std(ddof=0)) if len(num_df[c2].dropna()) else 0.0
                if m1 > m2 or (m1 == m2 and (s1 < s2 or (s1 == s2 and c1 > c2))):
                    to_drop, keep = c1, c2
                else:
                    to_drop, keep = c2, c1
                plan.append({
                    "column": to_drop,
                    "action": "drop_column",
                    "justification": f"La columna numérica '{to_drop}' está altamente correlacionada con '{keep}' (|corr|={corr_val:.4f} >= {drop_high_correlation_threshold}).",
                    "params": {
                        "reason": "high_correlation",
                        "correlated_with": keep,
                        "correlation": corr_val,
                        "threshold": drop_high_correlation_threshold,
                    },
                })
                dropped_corr.add(to_drop)
                early_dropped.add(to_drop)

    # Missing indicators and imputation (only for columns not dropped)
    dropped = early_dropped
    for name in df.columns:
        if str(name) in dropped:
            continue
        series = df[name]
        missing = int(series.isna().sum())
        if missing == 0:
            continue

        # Indicator
        plan.append({
            "column": str(name),
            "action": "add_missing_indicator",
            "justification": f"Marcar presencia de valores faltantes en '{name}' para preservar la señal de ausencia.",
        })

        # Imputation strategy
        is_numeric = pd.api.types.is_numeric_dtype(series) or pd.to_numeric(series, errors="coerce").notna().mean() > 0.8
        strat_key = "__numeric__" if is_numeric else "__categorical__"
        strat = strategies.get(str(name), strategies.get(strat_key, "median" if is_numeric else "mode"))
        if isinstance(strat, dict):
            strategy = strat.get("strategy", "constant")
            value = strat.get("value")
        else:
            strategy = strat
            value = None

        if strategy == "median" or (strategy is None and is_numeric):
            action = "impute_median"
            justification = f"Imputar mediana en '{name}' (estrategia por defecto para numéricas)."
        elif strategy == "mean":
            action = "impute_mean"
            justification = f"Imputar media en '{name}' según estrategia configurada."
        elif strategy == "mode":
            action = "impute_mode"
            justification = f"Imputar moda en '{name}' (estrategia por defecto para categóricas)."
        elif strategy == "constant":
            action = "impute_constant"
            justification = f"Imputar valor constante en '{name}' según estrategia configurada."
            params = {"value": value}
        else:
            action = "impute_median" if is_numeric else "impute_mode"
            justification = f"Imputar {action.replace('impute_', '')} en '{name}'."

        step = {
            "column": str(name),
            "action": action,
            "justification": justification,
        }
        if action == "impute_constant":
            step["params"] = {"value": value}
        plan.append(step)

    # Clip outliers IQR (on remaining numeric)
    for name in df.columns:
        if str(name) in dropped:
            continue
        series = df[name]
        numeric = pd.to_numeric(series, errors="coerce")
        valid = numeric.dropna()
        if len(valid) >= 8:
            q1, q3 = valid.quantile(0.25), valid.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outliers = int(((valid < lower) | (valid > upper)).sum())
                if outliers and outliers / len(valid) >= 0.01:
                    plan.append({
                        "column": str(name),
                        "action": "clip_outliers",
                        "justification": f"Recortar outliers por IQR (1.5·IQR) en '{name}' ({outliers} valores).",
                        "params": {"lower": float(lower), "upper": float(upper), "count": outliers},
                    })

    # Scale numeric
    if scale_numeric:
        for name in df.columns:
            if str(name) in dropped:
                continue
            series = df[name]
            numeric = pd.to_numeric(series, errors="coerce")
            valid = numeric.dropna()
            if len(valid) >= 2 and (pd.api.types.is_numeric_dtype(series) or (numeric.notna().mean() > 0.8)):
                mean = float(valid.mean())
                std = float(valid.std(ddof=0))  # population
                if std > 0:
                    plan.append({
                        "column": str(name),
                        "action": "scale_standard",
                        "justification": f"Estandarizar z-score (media={mean:.4f}, std={std:.4f}) la columna numérica '{name}'.",
                        "params": {"mean": mean, "std": std},
                    })

    # Encode categorical
    if encode_categorical in {"onehot", "ordinal"}:
        for name in df.columns:
            if str(name) in dropped:
                continue
            series = df[name]
            if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
                continue  # skip pure numeric
            # treat as categorical if object or low cardinality numeric? but tests are object
            cats = series.dropna().unique()
            if len(cats) == 0:
                continue
            if encode_categorical == "onehot":
                categories = sorted(str(c) for c in cats)
                if onehot_drop_first and categories:
                    dropped_cat = categories[0]
                    categories = categories[1:]
                    params = {"categories": categories, "drop_first": True, "dropped_category": dropped_cat}
                else:
                    params = {"categories": categories, "drop_first": False}
                plan.append({
                    "column": str(name),
                    "action": "encode_onehot",
                    "justification": f"Codificar one-hot la columna categórica '{name}'{' (drop_first)' if onehot_drop_first else ''}.",
                    "params": params,
                })
            else:  # ordinal
                # frequency descending, then alpha for stability
                vc = series.dropna().astype(str).value_counts()
                ordered = vc.index.tolist()  # already by count desc
                mapping = {cat: idx for idx, cat in enumerate(ordered)}
                plan.append({
                    "column": str(name),
                    "action": "encode_ordinal",
                    "justification": f"Codificar ordinal (por frecuencia descendente) la columna categórica '{name}'.",
                    "params": {"mapping": mapping},
                })

    return plan


def apply_plan(df: pd.DataFrame, plan: list[dict[str, Any]]) -> pd.DataFrame:
    """Apply the cleaning plan steps in order and return the cleaned DataFrame."""
    result = df.copy()
    for step in plan:
        action = step["action"]
        col = step.get("column")
        params = step.get("params") or {}

        if action == "drop_duplicates":
            result = result.drop_duplicates()
        elif action == "drop_column" and col and col in result.columns:
            result = result.drop(columns=[col])
        elif action == "add_missing_indicator" and col and col in result.columns:
            result[f"{col}__missing"] = result[col].isna().astype(int)
        elif action == "impute_median" and col and col in result.columns:
            med = result[col].median()
            result[col] = result[col].fillna(med)
        elif action == "impute_mean" and col and col in result.columns:
            mean = result[col].mean()
            result[col] = result[col].fillna(mean)
        elif action == "impute_mode" and col and col in result.columns:
            mode = result[col].mode(dropna=True)
            fill = mode.iloc[0] if len(mode) else None
            result[col] = result[col].fillna(fill)
        elif action == "impute_constant" and col and col in result.columns:
            result[col] = result[col].fillna(params.get("value"))
        elif action == "clip_outliers" and col and col in result.columns:
            lower = params.get("lower")
            upper = params.get("upper")
            if lower is not None and upper is not None:
                result[col] = result[col].clip(lower=lower, upper=upper)
        elif action == "scale_standard" and col and col in result.columns:
            mean = params.get("mean", 0.0)
            std = params.get("std", 1.0)
            if std and std != 0:
                result[col] = (result[col] - mean) / std
        elif action == "encode_onehot" and col and col in result.columns:
            categories = params.get("categories", [])
            drop_first = params.get("drop_first", False)
            # Imputation already done, so no NaNs expected
            dummies = pd.get_dummies(result[col].astype(str), prefix=col)
            # Keep only expected categories
            expected = [f"{col}_{c}" for c in categories]
            for exp in expected:
                if exp not in dummies.columns:
                    dummies[exp] = 0
            dummies = dummies[expected]
            result = result.drop(columns=[col]).join(dummies)
        elif action == "encode_ordinal" and col and col in result.columns:
            mapping = params.get("mapping", {})
            result[col] = result[col].astype(str).map(mapping).fillna(-1).astype(int)

    return result.reset_index(drop=True)


def quality_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Compute quality improvement delta between before and after profiles."""
    return {
        "rows_removed": before.get("rows", 0) - after.get("rows", 0),
        "columns_removed": before.get("columns", 0) - after.get("columns", 0),
        "duplicate_rows_after": after.get("duplicate_rows", 0),
        "issues_resolved": before.get("issue_count", 0) - after.get("issue_count", 0),
    }

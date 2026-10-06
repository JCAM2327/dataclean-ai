from __future__ import annotations

from typing import Any

import pandas as pd

# Nombres habituales de la variable a predecir. No sustituyen un --target explícito.
TARGET_ALIASES = {
    "target",
    "label",
    "y",
    "clase",
    "class",
    "outcome",
    "objetivo",
    "churn",
    "resultado",
    "respuesta",
}

SMALL_SAMPLE = 30
HIGH_MISSING_PCT = 40.0
IMBALANCE_RATIO = 0.2


def detect_target(df: pd.DataFrame, target: str | None = None) -> dict[str, Any]:
    """Detect a numeric or categorical target column.

    An explicit column name always wins when it exists. Otherwise the detector
    scores non-identifier columns and prefers known target names and low
    cardinality. The result declares kind (numeric|categorical) and task
    (regression|classification).
    """
    if df.empty or len(df.columns) == 0:
        return _empty("El dataset no tiene filas u columnas utilizables.")

    if target is not None:
        if target not in df.columns:
            return {
                "found": False,
                "column": target,
                "kind": None,
                "task": None,
                "confidence": 0.0,
                "source": "explicit",
                "rationale": f"La columna '{target}' no existe en el dataset.",
                "candidates": [],
                "warnings": ["target_missing"],
            }
        return _report_for(df, target, source="explicit", score=1.0, candidates=[])

    scored: list[dict[str, Any]] = []
    n_rows = len(df)
    for name in df.columns:
        series = df[name]
        column = str(name)
        kind = _kind(series)
        if kind is None:
            continue
        if _is_identifier(series, int(series.nunique(dropna=True)), n_rows):
            continue
        score, reasons = _score(series, kind)
        scored.append({
            "column": column,
            "kind": kind,
            "task": _task(kind),
            "score": round(score, 3),
            "rationale": "; ".join(reasons),
        })

    if not scored:
        return _empty("Ninguna columna es usable como objetivo (constantes o identificadores).")

    scored.sort(key=lambda item: (-item["score"], item["column"]))
    best = scored[0]
    report = _report_for(
        df,
        best["column"],
        source="inferred",
        score=best["score"],
        candidates=scored[:5],
    )
    if len(scored) > 1 and scored[1]["score"] >= best["score"] - 0.05 and best["score"] < 0.85:
        report["warnings"].append("ambiguous_target")
        report["confidence"] = round(min(report["confidence"], 0.55), 3)
        report["rationale"] += " Hay otro candidato con puntuación cercana; conviene fijar --target."
    return report


def _report_for(
    df: pd.DataFrame,
    column: str,
    source: str,
    score: float,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    series = df[column]
    kind = _kind(series)
    warnings: list[str] = []
    if kind is None:
        return {
            "found": False,
            "column": column,
            "kind": None,
            "task": None,
            "confidence": 0.0,
            "source": source,
            "rationale": f"'{column}' es constante o no tiene valores observados.",
            "candidates": candidates,
            "warnings": ["unusable_target"],
        }
    observed = series.dropna()
    missing_pct = 100 * int(series.isna().sum()) / len(df) if len(df) else 0.0
    if missing_pct >= HIGH_MISSING_PCT:
        warnings.append("high_missing_target")
    if len(df) < SMALL_SAMPLE:
        warnings.append("small_sample")
    balance = None
    if kind == "categorical":
        counts = observed.astype(str).value_counts(normalize=True)
        minority = float(counts.min()) if not counts.empty else 0.0
        balance = {
            "classes": int(observed.nunique()),
            "minority_ratio": round(minority, 4),
        }
        if minority < IMBALANCE_RATIO:
            warnings.append("class_imbalance")
    confidence = score if source == "inferred" else 1.0
    if "high_missing_target" in warnings:
        confidence = min(confidence, 0.6)
    rationale = _rationale(column, kind, source, int(observed.nunique()))
    return {
        "found": True,
        "column": column,
        "kind": kind,
        "task": _task(kind),
        "confidence": round(float(confidence), 3),
        "source": source,
        "classes": None if balance is None else balance["classes"],
        "minority_ratio": None if balance is None else balance["minority_ratio"],
        "missing_pct": round(missing_pct, 2),
        "unique": int(observed.nunique()),
        "rationale": rationale,
        "candidates": candidates,
        "warnings": warnings,
    }


def _score(series: pd.Series, kind: str) -> tuple[float, list[str]]:
    name = str(series.name).lower()
    reasons: list[str] = []
    score = 0.35
    if name in TARGET_ALIASES or name.endswith("_target") or name.startswith("target_"):
        score += 0.5
        reasons.append("el nombre coincide con un alias de objetivo")
    nunique = int(series.nunique(dropna=True))
    if kind == "categorical":
        score += 0.15
        reasons.append(f"cardinalidad baja ({nunique} clases)")
        if nunique == 2:
            score += 0.05
            reasons.append("binaria")
    else:
        reasons.append(f"numérica con {nunique} valores distintos")
        score += 0.05
    missing_pct = 100 * int(series.isna().sum()) / len(series) if len(series) else 0.0
    if missing_pct >= HIGH_MISSING_PCT:
        score -= 0.25
        reasons.append("nulos elevados")
    return max(0.0, min(score, 1.0)), reasons


def _kind(series: pd.Series) -> str | None:
    observed = series.dropna()
    if observed.empty or int(observed.nunique()) < 2:
        return None
    if pd.api.types.is_bool_dtype(series) or pd.api.types.is_bool_dtype(observed):
        return "categorical"
    numeric = pd.to_numeric(observed, errors="coerce")
    if float(numeric.notna().mean()) >= 0.8:
        integer_like = float((numeric.dropna() % 1 == 0).mean()) >= 0.95
        if integer_like and int(numeric.nunique()) <= 12:
            return "categorical"
    return "numeric" if float(numeric.notna().mean()) >= 0.8 else "categorical"


def _task(kind: str) -> str:
    return "classification" if kind == "categorical" else "regression"


def _is_identifier(series: pd.Series, nunique: int, n_rows: int) -> bool:
    name = str(series.name).lower()
    named_id = name in {"id", "uuid", "guid"} or name.endswith("_id")
    unique_text = nunique == n_rows and (
        pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series)
    )
    return named_id or unique_text


def _rationale(column: str, kind: str, source: str, nunique: int) -> str:
    origin = "indicada de forma explícita" if source == "explicit" else "inferida por nombre y cardinalidad"
    if kind == "categorical":
        return f"'{column}' es categórica ({nunique} clases), {origin}; tarea de clasificación."
    return f"'{column}' es numérica continua ({nunique} valores), {origin}; tarea de regresión."


def _empty(rationale: str) -> dict[str, Any]:
    return {
        "found": False,
        "column": None,
        "kind": None,
        "task": None,
        "confidence": 0.0,
        "source": "inferred",
        "rationale": rationale,
        "candidates": [],
        "warnings": ["target_not_found"],
    }

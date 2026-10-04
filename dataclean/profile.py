from __future__ import annotations

from typing import Any

import pandas as pd


def profile_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """Build a column-level profile for a tabular dataset."""
    n_rows, n_cols = df.shape
    columns: list[dict[str, Any]] = []
    for name in df.columns:
        series = df[name]
        missing = int(series.isna().sum())
        nunique = int(series.nunique(dropna=True))
        col: dict[str, Any] = {
            "name": str(name),
            "dtype": str(series.dtype),
            "missing": missing,
            "missing_pct": round(100 * missing / n_rows, 2) if n_rows else 0.0,
            "unique": nunique,
            "unique_pct": round(100 * nunique / n_rows, 2) if n_rows else 0.0,
        }
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().sum() >= max(1, int(0.8 * (series.notna().sum() or 1))):
            col["numeric"] = {
                "min": _num(numeric.min()),
                "max": _num(numeric.max()),
                "mean": _num(numeric.mean()),
                "median": _num(numeric.median()),
                "std": _num(numeric.std()),
            }
        columns.append(col)
    return {
        "rows": n_rows,
        "columns": n_cols,
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_bytes": int(df.memory_usage(deep=True).sum()),
        "column_profiles": columns,
    }


def _num(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return round(float(value), 6)

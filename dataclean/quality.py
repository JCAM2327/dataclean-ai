from __future__ import annotations

from typing import Any

import pandas as pd


def detect_issues(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Detect common data-quality issues. Each issue has severity and a fix hint."""
    issues: list[dict[str, Any]] = []
    n_rows = len(df)
    if n_rows == 0:
        return [{"code": "empty_frame", "severity": "critical", "column": None, "message": "El dataset no tiene filas."}]

    dup = int(df.duplicated().sum())
    if dup:
        issues.append({
            "code": "duplicate_rows",
            "severity": "medium",
            "column": None,
            "count": dup,
            "message": f"{dup} filas duplicadas ({round(100 * dup / n_rows, 2)}%).",
            "recommendation": "Revisar clave de negocio y eliminar duplicados exactos si no aportan.",
        })

    for name in df.columns:
        series = df[name]
        missing = int(series.isna().sum())
        missing_pct = 100 * missing / n_rows
        if missing_pct >= 40:
            issues.append({
                "code": "high_missing",
                "severity": "high",
                "column": str(name),
                "missing_pct": round(missing_pct, 2),
                "message": f"'{name}' tiene {round(missing_pct, 2)}% de nulos.",
                "recommendation": "Valorar dropear la columna o imputar solo si el mecanismo de faltantes es entendible.",
            })
        elif missing_pct > 0:
            issues.append({
                "code": "some_missing",
                "severity": "low",
                "column": str(name),
                "missing_pct": round(missing_pct, 2),
                "message": f"'{name}' tiene {round(missing_pct, 2)}% de nulos.",
                "recommendation": "Imputar con mediana/moda o marcar un indicador de faltante.",
            })

        nunique = int(series.nunique(dropna=True))
        if nunique == 1 and missing < n_rows:
            issues.append({
                "code": "constant_column",
                "severity": "medium",
                "column": str(name),
                "message": f"'{name}' es constante.",
                "recommendation": "No aporta señal para modelos; se puede excluir del feature set.",
            })
        if nunique == n_rows and series.dtype == object:
            issues.append({
                "code": "likely_id",
                "severity": "low",
                "column": str(name),
                "message": f"'{name}' parece un identificador (único por fila).",
                "recommendation": "No usarla como feature de modelo salvo para joins.",
            })

        numeric = pd.to_numeric(series, errors="coerce")
        valid = numeric.dropna()
        if len(valid) >= 8:
            q1, q3 = valid.quantile(0.25), valid.quantile(0.75)
            iqr = q3 - q1
            if iqr > 0:
                outliers = int(((valid < q1 - 1.5 * iqr) | (valid > q3 + 1.5 * iqr)).sum())
                if outliers and outliers / len(valid) >= 0.01:
                    issues.append({
                        "code": "iqr_outliers",
                        "severity": "low",
                        "column": str(name),
                        "count": outliers,
                        "message": f"'{name}' tiene {outliers} outliers por IQR.",
                        "recommendation": "Revisar si son errores o colas reales antes de winsorizar.",
                    })
    return issues

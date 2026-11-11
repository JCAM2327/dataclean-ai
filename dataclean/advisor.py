from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


def suggest_modeling_strategy(
    df: pd.DataFrame,
    target_report: dict[str, Any] | None,
    model_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Suggest next modeling or unsupervised analysis steps based on data and prior reports.

    Returns a structured recommendation covering supervised continuation,
    unsupervised clustering viability (with optional KMeans evaluation), and concrete next actions.
    """
    n_rows = int(len(df))
    numeric_cols = [
        col for col in df.columns
        if pd.api.types.is_numeric_dtype(df[col]) and df[col].nunique(dropna=True) > 1
    ]
    n_numeric = len(numeric_cols)

    target_found = bool(target_report and target_report.get("found"))
    model_status = (model_report or {}).get("status")

    recommendations: list[str] = []
    strategy = "insufficient"
    clustering_viable = n_numeric >= 2 and n_rows >= 20
    clustering_results: dict[str, Any] | None = None

    if target_found and model_status == "compared":
        strategy = "supervised"
        lift = float((model_report or {}).get("lift_vs_baseline") or 0)
        winner = (model_report or {}).get("winner")
        if lift > 0.05:
            recommendations.append(
                f"El modelo {winner} supera al baseline; considerar validación cruzada o modelos más expresivos."
            )
        else:
            recommendations.append(
                "La mejora sobre el baseline es limitada; revisar features, balance de clases o tamaño de muestra."
            )
        if (model_report or {}).get("warnings"):
            recommendations.append(
                "Atender advertencias del informe de modelado antes de producción."
            )
    elif target_found:
        strategy = "supervised"
        recommendations.append(
            "Variable objetivo detectada pero modelado no comparado; ejecutar comparación de baselines."
        )
    else:
        strategy = "unsupervised" if clustering_viable else "insufficient"
        recommendations.append(
            "No se detectó variable objetivo clara; considerar análisis no supervisado."
        )

    if clustering_viable and strategy != "supervised":
        recommendations.append(
            f"Clustering viable: {n_numeric} columnas numéricas con variación y {n_rows} filas. "
            "Probar KMeans con k=2..5 y evaluar silueta."
        )
        # Evaluación mínima de clustering
        X = df[numeric_cols].dropna()
        if len(X) >= 20:
            try:
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(X)
                scores: dict[int, float] = {}
                best_k: int | None = None
                best_score = -1.0
                best_labels: list[int] | None = None
                max_k = min(5, max(2, len(X) // 5))
                for k in range(2, max_k + 1):
                    km = KMeans(n_clusters=k, random_state=42, n_init=10)
                    labels = km.fit_predict(X_scaled)
                    score = float(silhouette_score(X_scaled, labels))
                    scores[k] = round(score, 4)
                    if score > best_score:
                        best_score = score
                        best_k = k
                        best_labels = labels.tolist()
                if best_k is not None and best_labels is not None:
                    clustering_results = {
                        "best_k": best_k,
                        "best_silhouette": round(best_score, 4),
                        "silhouette_scores": scores,
                        "n_samples": int(len(X)),
                        "labels": best_labels,
                    }
                    recommendations.append(
                        f"Evaluación KMeans: mejor k={best_k} con silueta {best_score:.3f}."
                    )
            except Exception:
                clustering_results = {"error": "No se pudo evaluar clustering"}
    elif not clustering_viable and not target_found:
        recommendations.append(
            "Datos insuficientes o con pocas variables numéricas para clustering confiable."
        )

    if n_rows < 30:
        recommendations.append("Muestra pequeña: priorizar modelos simples e interpretar con cautela.")

    rationale = (
        f"Estrategia sugerida: {strategy}. "
        f"Filas={n_rows}, columnas numéricas utilizables={n_numeric}."
    )

    result: dict[str, Any] = {
        "strategy": strategy,
        "clustering_viable": clustering_viable,
        "numeric_columns_count": n_numeric,
        "rows": n_rows,
        "recommendations": recommendations,
        "rationale": rationale,
        "target_found": target_found,
    }
    if clustering_results is not None:
        result["clustering_results"] = clustering_results
    return result

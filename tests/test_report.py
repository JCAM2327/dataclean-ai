"""Pruebas del renderizado de informes HTML."""

from dataclean.report import render_report_html


def test_html_includes_aggregated_importance_bars():
    record = {
        "filename": "test.csv",
        "dataset_id": "abc",
        "created_at": "2026-11-06",
        "applied": False,
        "summary": {"issue_count": 0},
        "report": {
            "issues": [],
            "plan": [],
            "target": {"found": False},
            "modeling": {
                "status": "compared",
                "task": "classification",
                "rows_used": 50,
                "winner": "regresion_logistica",
                "lift_vs_baseline": 0.1,
                "aggregated_importances": [
                    {"feature": "edad", "max_importance": 0.45, "mean_importance": 0.3, "model_count": 2},
                    {"feature": "ingreso", "max_importance": 0.35, "mean_importance": 0.25, "model_count": 2},
                ],
            },
        },
    }
    html = render_report_html(record)
    assert "bar-row" in html
    assert "bar-track" in html
    assert "edad" in html
    assert "Visualización (importancia máxima)" in html


def test_html_includes_cluster_distribution():
    record = {
        "filename": "test.csv",
        "dataset_id": "abc",
        "created_at": "2026-11-14",
        "applied": False,
        "summary": {"issue_count": 0},
        "report": {
            "issues": [],
            "plan": [],
            "target": {"found": False},
            "modeling": {},
        },
        "advisor": {
            "strategy": "unsupervised",
            "clustering_viable": True,
            "clustering_results": {
                "best_k": 2,
                "best_silhouette": 0.45,
                "best_inertia": 12.34,
                "n_samples": 10,
                "labels": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
            },
        },
    }
    html = render_report_html(record)
    assert "Distribución de etiquetas de cluster" in html
    assert "Cluster" in html
    assert "Conteo" in html
    assert "Porcentaje" in html
    assert "50.0%" in html
    assert "Inercia" in html
    assert "12.34" in html

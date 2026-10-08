import numpy as np
import pandas as pd

from dataclean.models import compare_models

def _classification_frame(n: int = 80) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    edad = rng.integers(18, 70, n)
    ingreso = edad * 1.4 + rng.normal(0, 5, n)
    objetivo = (ingreso > np.median(ingreso)).astype(int)
    return pd.DataFrame({
        "id": [f"u{i}" for i in range(n)],
        "edad": edad,
        "ingreso": ingreso,
        "objetivo": objetivo,
    })


def test_classification_compares_majority_baseline_and_two_models():
    df = _classification_frame()
    report = compare_models(df, {"found": True, "column": "objetivo", "task": "classification", "warnings": []})
    assert report["status"] == "compared"
    assert report["task"] == "classification"
    assert report["baseline"]["name"] == "baseline_mayoria"
    assert report["baseline"]["role"] == "baseline"
    names = [item["name"] for item in report["models"]]
    assert names == ["regresion_logistica", "arbol_profundidad_3"]
    assert report["primary_metric"] == "f1_macro"
    assert set(report["baseline"]["metrics"]) == {"accuracy", "f1_macro", "f1_weighted"}
    assert report["winner"] in {"baseline_mayoria", "regresion_logistica", "arbol_profundidad_3"}
    assert "id" in report["features_dropped"]
    assert report["beats_baseline"] is True
    assert report["lift_vs_baseline"] > 0


def test_regression_compares_mean_baseline():
    rng = np.random.default_rng(3)
    x = rng.normal(0, 1, 60)
    y = 3 * x + rng.normal(0, 0.2, 60)
    df = pd.DataFrame({"x": x, "ingreso": y, "constante": 1})
    report = compare_models(df, {"found": True, "column": "ingreso", "task": "regression", "warnings": []})
    assert report["status"] == "compared"
    assert report["task"] == "regression"
    assert report["baseline"]["name"] == "baseline_media"
    assert [item["name"] for item in report["models"]] == ["regresion_lineal", "arbol_profundidad_3"]
    assert report["primary_metric"] == "rmse"
    assert report["higher_is_better"] is False
    assert "constante" in report["features_dropped"]
    assert report["winner"] == "regresion_lineal"
    assert report["beats_baseline"] is True


def test_skips_without_usable_target():
    df = pd.DataFrame({"id": ["a", "b", "c"], "pais": ["AR", "AR", "AR"]})
    report = compare_models(df, {"found": False, "column": None, "task": None, "warnings": ["target_not_found"]})
    assert report["status"] == "skipped"
    assert report["models"] == []
    assert report["baseline"] is None
    assert "target_not_found" in report["warnings"]


def test_metrics_report_keeps_small_sample_and_imbalance_warnings():
    df = pd.DataFrame({
        "feature": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "objetivo": [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    })
    report = compare_models(df, {"found": True, "column": "objetivo", "task": "classification", "warnings": ["small_sample", "class_imbalance"]})
    assert report["status"] == "compared"
    assert "small_sample" in report["warnings"]
    assert "class_imbalance" in report["warnings"]
    assert report["split"]["train_rows"] + report["split"]["test_rows"] == 10
    assert report["rationale"]


def test_skips_when_only_identifier_features_remain():
    df = pd.DataFrame({
        "id": [f"u{i}" for i in range(12)],
        "objetivo": [0, 1] * 6,
    })
    report = compare_models(df, {"found": True, "column": "objetivo", "task": "classification", "warnings": []})
    assert report["status"] == "skipped"
    assert "insufficient_features" in report["warnings"]

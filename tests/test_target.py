import pandas as pd

from dataclean.target import detect_target


def test_infers_named_binary_target_as_classification():
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5, 6],
        "edad": [30, 41, 22, 55, 33, 47],
        "ciudad": ["A", "B", "A", "B", "A", "C"],
        "objetivo": [1, 0, 0, 1, 0, 1],
    })
    report = detect_target(df)
    assert report["found"] is True
    assert report["column"] == "objetivo"
    assert report["kind"] == "categorical"
    assert report["task"] == "classification"
    assert report["source"] == "inferred"
    assert report["classes"] == 2
    assert "id" not in {item["column"] for item in report["candidates"]}


def test_explicit_numeric_target_is_regression():
    df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5, 6, 7, 8],
        "ingreso": [10.5, 11.0, 9.2, 14.4, 8.1, 12.0, 13.3, 7.7],
        "objetivo": [0, 1, 0, 1, 0, 1, 0, 1],
    })
    report = detect_target(df, target="ingreso")
    assert report["found"] is True
    assert report["column"] == "ingreso"
    assert report["kind"] == "numeric"
    assert report["task"] == "regression"
    assert report["source"] == "explicit"
    assert report["confidence"] == 1.0


def test_missing_explicit_target():
    df = pd.DataFrame({"a": [1, 2, 3], "b": [0, 1, 0]})
    report = detect_target(df, target="y")
    assert report["found"] is False
    assert report["column"] == "y"
    assert "target_missing" in report["warnings"]


def test_rejects_constant_and_identifier_only_frames():
    df = pd.DataFrame({"id": ["a", "b", "c"], "pais": ["AR", "AR", "AR"]})
    report = detect_target(df)
    assert report["found"] is False
    assert "target_not_found" in report["warnings"]


def test_small_sample_and_imbalance_warnings():
    df = pd.DataFrame({
        "feature": [1, 2, 3, 4, 5, 6],
        "objetivo": [1, 0, 0, 0, 0, 0],
    })
    report = detect_target(df)
    assert report["column"] == "objetivo"
    assert "small_sample" in report["warnings"]
    assert "class_imbalance" in report["warnings"]
    assert report["minority_ratio"] < 0.2

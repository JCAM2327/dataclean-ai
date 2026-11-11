import pandas as pd

from dataclean.advisor import suggest_modeling_strategy


def test_suggest_supervised_when_target_and_model():
    df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5],
        "y": [0, 1, 0, 1, 0],
    })
    target = {"found": True, "column": "y", "task": "classification"}
    model = {
        "status": "compared",
        "winner": "arbol_profundidad_3",
        "lift_vs_baseline": 0.12,
        "warnings": [],
    }
    result = suggest_modeling_strategy(df, target, model)
    assert result["strategy"] == "supervised"
    assert result["target_found"] is True
    assert any("supera al baseline" in r for r in result["recommendations"])


def test_suggest_unsupervised_when_no_target():
    df = pd.DataFrame({
        "a": list(range(30)),
        "b": list(range(30, 60)),
        "c": ["x"] * 30,
    })
    result = suggest_modeling_strategy(df, None, None)
    assert result["strategy"] == "unsupervised"
    assert result["clustering_viable"] is True
    assert result["numeric_columns_count"] == 2
    assert any("Clustering viable" in r for r in result["recommendations"])
    cr = result.get("clustering_results")
    assert cr is not None
    assert "labels" in cr
    assert isinstance(cr["labels"], list)
    assert len(cr["labels"]) == cr["n_samples"]
    assert all(isinstance(l, int) for l in cr["labels"])


def test_insufficient_small_data():
    df = pd.DataFrame({"a": [1, 2, 3]})
    result = suggest_modeling_strategy(df, None, None)
    assert result["strategy"] == "insufficient"
    assert result["clustering_viable"] is False

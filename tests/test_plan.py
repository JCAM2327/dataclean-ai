import pandas as pd

from dataclean.plan import apply_plan, build_cleaning_plan, quality_delta
from dataclean.profile import profile_dataframe
from dataclean.quality import detect_issues


def test_plan_lists_column_action_and_justification():
    df = pd.DataFrame({
        "id": [1, 1, 2, 3],
        "edad": [30, 30, None, 40],
        "ciudad": ["A", "A", "A", "A"],
        "codigo": ["x1", "x1", "x2", "x3"],
    })
    plan = build_cleaning_plan(df)
    assert plan
    for step in plan:
        assert "column" in step
        assert step["action"]
        assert step["justification"]

    actions = {(step["column"], step["action"]) for step in plan}
    assert (None, "drop_duplicates") in actions
    assert ("ciudad", "drop_column") in actions
    assert ("id", "drop_column") in actions
    assert ("edad", "impute_median") in actions
    assert ("edad", "add_missing_indicator") in actions


def test_apply_plan_cleans_and_reports_delta():
    df = pd.DataFrame({
        "id": ["a", "a", "b", "c"],
        "edad": [30, 30, None, 40],
        "ciudad": ["MDQ", "MDQ", "MDQ", "MDQ"],
        "segmento": ["x", "x", "y", None],
    })
    before = {
        "rows": len(df),
        "columns": df.shape[1],
        "duplicate_rows": int(df.duplicated().sum()),
        "issue_count": len(detect_issues(df)),
    }
    plan = build_cleaning_plan(df)
    cleaned = apply_plan(df, plan)
    after_profile = profile_dataframe(cleaned)
    after = {
        "rows": after_profile["rows"],
        "columns": after_profile["columns"],
        "duplicate_rows": after_profile["duplicate_rows"],
        "issue_count": len(detect_issues(cleaned)),
    }
    delta = quality_delta(before, after)

    assert cleaned.duplicated().sum() == 0
    assert "ciudad" not in cleaned.columns
    assert "id" not in cleaned.columns
    assert cleaned["edad"].isna().sum() == 0
    assert "edad__missing" in cleaned.columns
    assert bool((cleaned.loc[cleaned["edad__missing"] == 1, "edad__missing"] == 1).all())
    assert cleaned["segmento"].isna().sum() == 0
    assert delta["rows_removed"] == 1
    assert delta["duplicate_rows_after"] == 0
    assert delta["issues_resolved"] > 0


def test_clip_outliers_iqr():
    df = pd.DataFrame({
        "valor": [10, 12, 11, 13, 1000, 9, 14, 10, 11, 12],
    })
    plan = build_cleaning_plan(df)
    clip_steps = [s for s in plan if s["action"] == "clip_outliers"]
    assert len(clip_steps) == 1
    step = clip_steps[0]
    assert step["column"] == "valor"
    assert "lower" in step["params"]
    assert "upper" in step["params"]
    assert step["params"]["count"] >= 1

    cleaned = apply_plan(df, plan)
    lower = step["params"]["lower"]
    upper = step["params"]["upper"]
    assert cleaned["valor"].max() <= upper
    assert cleaned["valor"].min() >= lower
    assert cleaned["valor"].max() < 1000


def test_configurable_imputation_strategies():
    df = pd.DataFrame({
        "edad": [10, None, 30, 40],
        "ciudad": ["X", None, "X", "Y"],
    })
    strategies = {
        "__numeric__": "mean",
        "__categorical__": {"strategy": "constant", "value": "Unknown"},
    }
    plan = build_cleaning_plan(df, strategies)
    actions = {(s["column"], s["action"]) for s in plan}
    assert ("edad", "impute_mean") in actions
    assert ("ciudad", "impute_constant") in actions

    cleaned = apply_plan(df, plan)
    assert cleaned["edad"].isna().sum() == 0
    assert abs(cleaned["edad"].iloc[1] - 26.666667) < 0.01  # mean of 10,30,40
    assert cleaned["ciudad"].iloc[1] == "Unknown"
    assert cleaned["edad__missing"].iloc[1] == 1
    assert cleaned["ciudad__missing"].iloc[1] == 1


def test_scale_numeric_standardization():
    df = pd.DataFrame({
        "valor": [10.0, 20.0, 30.0, 40.0],
        "categoria": ["a", "b", "a", "c"],
    })
    plan = build_cleaning_plan(df, scale_numeric=True)
    scale_steps = [s for s in plan if s["action"] == "scale_standard"]
    assert len(scale_steps) == 1
    step = scale_steps[0]
    assert step["column"] == "valor"
    assert "mean" in step["params"]
    assert "std" in step["params"]
    mean = step["params"]["mean"]
    std = step["params"]["std"]
    assert abs(mean - 25.0) < 0.01
    assert abs(std - 11.18034) < 0.1  # population std of [10,20,30,40]

    cleaned = apply_plan(df, plan)
    expected = (df["valor"] - mean) / std
    assert (cleaned["valor"] - expected).abs().max() < 1e-6
    # Categorical unchanged
    assert list(cleaned["categoria"]) == list(df["categoria"])
    # Default (scale_numeric=False) does not add the step
    plan_off = build_cleaning_plan(df, scale_numeric=False)
    assert not any(s["action"] == "scale_standard" for s in plan_off)


def test_encode_categorical_onehot_and_ordinal():
    df = pd.DataFrame({
        "categoria": ["a", "b", "a", "c", "b", None],
        "valor": [1, 2, 3, 4, 5, 6],
    })
    # one-hot
    plan_oh = build_cleaning_plan(df, encode_categorical="onehot")
    oh_steps = [s for s in plan_oh if s["action"] == "encode_onehot"]
    assert len(oh_steps) == 1
    step = oh_steps[0]
    assert step["column"] == "categoria"
    cats = step["params"]["categories"]
    assert set(cats) == {"a", "b", "c"}

    cleaned_oh = apply_plan(df, plan_oh)
    assert "categoria" not in cleaned_oh.columns
    for cat in ["a", "b", "c"]:
        assert f"categoria_{cat}" in cleaned_oh.columns
    # Imputation of mode ("a") occurs before encoding, so 3 a's
    assert cleaned_oh["categoria_a"].sum() == 3
    assert cleaned_oh["categoria_b"].sum() == 2
    assert cleaned_oh["categoria_c"].sum() == 1
    # original numeric preserved
    assert "valor" in cleaned_oh.columns

    # ordinal
    plan_ord = build_cleaning_plan(df, encode_categorical="ordinal")
    ord_steps = [s for s in plan_ord if s["action"] == "encode_ordinal"]
    assert len(ord_steps) == 1
    mapping = ord_steps[0]["params"]["mapping"]
    # frequency: a:2, b:2, c:1 → a and b get 0/1 (order by value_counts which is stable-ish)
    assert set(mapping.keys()) == {"a", "b", "c"}
    assert all(v in {0, 1, 2} for v in mapping.values())

    cleaned_ord = apply_plan(df, plan_ord)
    assert "categoria" in cleaned_ord.columns
    assert cleaned_ord["categoria"].dtype == int
    assert set(cleaned_ord["categoria"].unique()) <= set(mapping.values())
    # No -1 because imputation precedes encoding
    assert (cleaned_ord["categoria"] == -1).sum() == 0

    # default does not encode
    plan_none = build_cleaning_plan(df)
    assert not any(s["action"] in {"encode_onehot", "encode_ordinal"} for s in plan_none)


def test_onehot_drop_first():
    df = pd.DataFrame({
        "categoria": ["a", "b", "a", "c", "b"],
        "valor": [1, 2, 3, 4, 5],
    })
    plan = build_cleaning_plan(df, encode_categorical="onehot", onehot_drop_first=True)
    steps = [s for s in plan if s["action"] == "encode_onehot"]
    assert len(steps) == 1
    step = steps[0]
    assert step["params"].get("drop_first") is True
    cats = step["params"]["categories"]
    # sorted: a, b, c → drop a
    assert set(cats) == {"b", "c"}
    assert step["params"].get("dropped_category") == "a"

    cleaned = apply_plan(df, plan)
    assert "categoria" not in cleaned.columns
    assert "categoria_a" not in cleaned.columns
    assert "categoria_b" in cleaned.columns
    assert "categoria_c" in cleaned.columns
    # All zeros for reference category 'a'
    a_rows = df["categoria"] == "a"
    assert cleaned.loc[a_rows, ["categoria_b", "categoria_c"]].sum().sum() == 0
    assert cleaned["categoria_b"].sum() == 2
    assert cleaned["categoria_c"].sum() == 1

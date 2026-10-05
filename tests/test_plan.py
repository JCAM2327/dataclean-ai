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

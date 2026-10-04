import pandas as pd

from dataclean.quality import detect_issues


def test_detects_duplicates_and_missing():
    df = pd.DataFrame({"id": [1, 1, 2], "edad": [30, 30, None], "ciudad": ["A", "A", "A"]})
    codes = {issue["code"] for issue in detect_issues(df)}
    assert "duplicate_rows" in codes
    assert "some_missing" in codes
    assert "constant_column" in codes

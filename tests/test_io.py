"""Pruebas del cargador de formatos tabulares."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import pytest

from dataclean.io import SUPPORTED_EXTENSIONS, load_dataframe


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2, None], "b": ["x", "y", "z"]})


def test_load_csv_path(tmp_path: Path):
    path = tmp_path / "sample.csv"
    _sample_df().to_csv(path, index=False)
    df = load_dataframe(path)
    assert list(df.columns) == ["a", "b"]
    assert len(df) == 3


def test_load_excel_path(tmp_path: Path):
    path = tmp_path / "sample.xlsx"
    _sample_df().to_excel(path, index=False, engine="openpyxl")
    df = load_dataframe(path)
    assert list(df.columns) == ["a", "b"]
    assert len(df) == 3


def test_load_parquet_path(tmp_path: Path):
    path = tmp_path / "sample.parquet"
    _sample_df().to_parquet(path, index=False)
    df = load_dataframe(path)
    assert list(df.columns) == ["a", "b"]
    assert len(df) == 3


def test_load_bytes_csv():
    buf = io.BytesIO()
    _sample_df().to_csv(buf, index=False)
    df = load_dataframe(buf.getvalue(), filename="sample.csv")
    assert len(df) == 3


def test_unsupported_extension_raises():
    with pytest.raises(ValueError, match="no soportado"):
        load_dataframe("/tmp/file.txt")


def test_supported_extensions_constant():
    assert ".csv" in SUPPORTED_EXTENSIONS
    assert ".xlsx" in SUPPORTED_EXTENSIONS
    assert ".parquet" in SUPPORTED_EXTENSIONS

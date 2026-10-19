"""Carga de datasets en formatos tabulares soportados."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".parquet"}


def load_dataframe(source: str | Path | bytes, filename: str | None = None) -> pd.DataFrame:
    """Carga un DataFrame desde ruta, Path o bytes, detectando el formato por extensión.

    Parameters
    ----------
    source
        Ruta de archivo, Path o contenido en bytes.
    filename
        Nombre de archivo (necesario cuando source es bytes) para inferir la extensión.

    Returns
    -------
    pd.DataFrame

    Raises
    ------
    ValueError
        Si la extensión no está soportada o no se puede inferir.
    """
    if isinstance(source, (str, Path)):
        path = Path(source)
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Formato no soportado: {ext or '(sin extensión)'}. "
                f"Soportados: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )
        if ext == ".csv":
            return pd.read_csv(path)
        if ext in {".xlsx", ".xls"}:
            return pd.read_excel(path)
        if ext == ".parquet":
            return pd.read_parquet(path)
        raise ValueError(f"Extensión no manejada: {ext}")

    # Bytes
    if not filename:
        raise ValueError("Se requiere filename cuando se cargan bytes")
    ext = Path(filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Formato no soportado: {ext or '(sin extensión)'}. "
            f"Soportados: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )
    buf = io.BytesIO(source)
    if ext == ".csv":
        return pd.read_csv(buf)
    if ext in {".xlsx", ".xls"}:
        return pd.read_excel(buf)
    if ext == ".parquet":
        return pd.read_parquet(buf)
    raise ValueError(f"Extensión no manejada: {ext}")

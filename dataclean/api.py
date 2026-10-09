from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from dataclean import __version__
from dataclean.cli import analyze_frame

MAX_UPLOAD_BYTES = 2_000_000
CSV_SUFFIXES = {".csv"}


class DatasetStore:
    """In-memory registry of uploaded datasets.

    Persistence of reports is a later phase item. This store keeps the upload
    contract testable without writing to disk.
    """

    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}

    def add(self, record: dict[str, Any]) -> dict[str, Any]:
        self._items[record["dataset_id"]] = record
        return record

    def get(self, dataset_id: str) -> dict[str, Any] | None:
        return self._items.get(dataset_id)

    def list(self) -> list[dict[str, Any]]:
        return [self._public(item) for item in self._items.values()]

    def clear(self) -> None:
        self._items.clear()

    @staticmethod
    def _public(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "dataset_id": item["dataset_id"],
            "filename": item["filename"],
            "created_at": item["created_at"],
            "rows": item["rows"],
            "columns": item["columns"],
            "applied": item["applied"],
            "summary": item["summary"],
        }


store = DatasetStore()
app = FastAPI(
    title="DataClean AI",
    version=__version__,
    description="Carga de datasets tabulares y generación del informe de perfil, plan y modelado.",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/datasets")
def list_datasets() -> dict[str, Any]:
    items = store.list()
    return {"count": len(items), "datasets": items}


@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str) -> dict[str, Any]:
    record = store.get(dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado.")
    return {
        "dataset_id": record["dataset_id"],
        "filename": record["filename"],
        "created_at": record["created_at"],
        "rows": record["rows"],
        "columns": record["columns"],
        "applied": record["applied"],
        "summary": record["summary"],
        "report": record["report"],
    }


@app.get("/datasets/{dataset_id}/cleaned", response_class=PlainTextResponse)
def get_cleaned(dataset_id: str) -> str:
    record = store.get(dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado.")
    if not record["applied"] or record["cleaned_csv"] is None:
        raise HTTPException(status_code=404, detail="Este dataset no tiene CSV limpio aplicado.")
    return record["cleaned_csv"]


@app.post("/datasets", status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    apply: bool = Form(False),
    target: str | None = Form(None),
) -> dict[str, Any]:
    filename = file.filename or "dataset.csv"
    suffix = _suffix(filename)
    if suffix not in CSV_SUFFIXES:
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos CSV.")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"El archivo supera el límite de {MAX_UPLOAD_BYTES} bytes.",
        )

    frame = _read_csv(payload)
    if frame.empty or frame.shape[1] == 0:
        raise HTTPException(status_code=422, detail="El CSV no contiene filas o columnas.")

    declared_target = target.strip() if target and target.strip() else None
    report, cleaned = analyze_frame(
        frame,
        source=filename,
        apply=apply,
        target=declared_target,
    )
    dataset_id = uuid.uuid4().hex
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    cleaned_csv = None if cleaned is None else cleaned.to_csv(index=False)
    record = store.add({
        "dataset_id": dataset_id,
        "filename": filename,
        "created_at": created_at,
        "rows": int(frame.shape[0]),
        "columns": int(frame.shape[1]),
        "applied": cleaned is not None,
        "summary": report["summary"],
        "report": report,
        "cleaned_csv": cleaned_csv,
    })
    return {
        "dataset_id": record["dataset_id"],
        "filename": record["filename"],
        "created_at": record["created_at"],
        "rows": record["rows"],
        "columns": record["columns"],
        "applied": record["applied"],
        "summary": record["summary"],
        "report_url": f"/datasets/{dataset_id}",
    }


def _suffix(filename: str) -> str:
    dot = filename.rfind(".")
    if dot < 0:
        return ""
    return filename[dot:].lower()


def _read_csv(payload: bytes) -> pd.DataFrame:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=422, detail="El CSV debe estar codificado en UTF-8.") from exc
    _reject_ragged_rows(text)
    try:
        return pd.read_csv(io.StringIO(text), on_bad_lines="error")
    except (pd.errors.ParserError, pd.errors.EmptyDataError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="No se pudo interpretar el CSV.") from exc


def _reject_ragged_rows(text: str) -> None:
    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration as exc:
        raise HTTPException(status_code=422, detail="No se pudo interpretar el CSV.") from exc
    width = len(header)
    if width == 0:
        raise HTTPException(status_code=422, detail="No se pudo interpretar el CSV.")
    for row in reader:
        if not row:
            continue
        if len(row) != width:
            raise HTTPException(status_code=422, detail="No se pudo interpretar el CSV.")

from __future__ import annotations

import csv
import io
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

from dataclean import __version__
from dataclean.cli import analyze_frame

MAX_UPLOAD_BYTES = 2_000_000
CSV_SUFFIXES = {".csv"}
DEFAULT_STORE_ROOT = Path("data/datasets")


class DatasetStore:
    """File-based registry of uploaded datasets.

    Each dataset is stored under ``root / dataset_id`` as:
    - ``meta.json``: metadata, summary and full report
    - ``original.csv``: original tabular data
    - ``cleaned.csv``: optional cleaned data after plan acceptance or application

    The store survives process restarts. The original frame is reconstructed
    from ``original.csv`` when needed for plan acceptance.
    """

    def __init__(self, root: Path | str = DEFAULT_STORE_ROOT) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def add(self, record: dict[str, Any]) -> dict[str, Any]:
        self._save(record)
        return record

    def get(self, dataset_id: str) -> dict[str, Any] | None:
        dataset_dir = self.root / dataset_id
        meta_path = dataset_dir / "meta.json"
        if not meta_path.is_file():
            return None
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        original_path = dataset_dir / "original.csv"
        if original_path.is_file():
            meta["frame"] = pd.read_csv(original_path)
        else:
            meta["frame"] = None
        cleaned_path = dataset_dir / "cleaned.csv"
        if cleaned_path.is_file():
            meta["cleaned_csv"] = cleaned_path.read_text(encoding="utf-8")
        else:
            meta["cleaned_csv"] = None
        return meta

    def list(self) -> list[dict[str, Any]]:
        items = []
        if not self.root.is_dir():
            return items
        for dataset_dir in sorted(self.root.iterdir()):
            if not dataset_dir.is_dir():
                continue
            meta_path = dataset_dir / "meta.json"
            if not meta_path.is_file():
                continue
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            items.append(self._public(meta))
        return items

    def clear(self) -> None:
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir(parents=True, exist_ok=True)

    def update(self, record: dict[str, Any]) -> None:
        """Persist an updated record (used after plan acceptance)."""
        self._save(record)

    def _save(self, record: dict[str, Any]) -> None:
        dataset_id = record["dataset_id"]
        dataset_dir = self.root / dataset_id
        dataset_dir.mkdir(parents=True, exist_ok=True)

        frame = record.get("frame")
        if frame is not None:
            frame.to_csv(dataset_dir / "original.csv", index=False)

        cleaned_csv = record.get("cleaned_csv")
        cleaned_path = dataset_dir / "cleaned.csv"
        if cleaned_csv is not None:
            cleaned_path.write_text(cleaned_csv, encoding="utf-8")
        elif cleaned_path.exists():
            cleaned_path.unlink()

        meta = {
            k: v
            for k, v in record.items()
            if k not in ("frame", "cleaned_csv")
        }
        (dataset_dir / "meta.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

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
    description="Carga de datasets tabulares, revisión del plan de limpieza, aceptación y persistencia de informes.",
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


@app.get("/datasets/{dataset_id}/review")
def review_dataset(dataset_id: str) -> dict[str, Any]:
    record = store.get(dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado.")
    return {
        "dataset_id": record["dataset_id"],
        "filename": record["filename"],
        "applied": record["applied"],
        "issues": record["report"]["issues"],
        "plan": record["report"]["plan"],
        "summary": record["summary"],
    }


@app.post("/datasets/{dataset_id}/accept", status_code=200)
def accept_plan(dataset_id: str) -> dict[str, Any]:
    record = store.get(dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado.")
    if record["applied"]:
        raise HTTPException(status_code=409, detail="El plan ya fue aceptado y aplicado.")
    frame = record["frame"]
    if frame is None:
        raise HTTPException(status_code=500, detail="Datos originales no disponibles para aplicar el plan.")
    report, cleaned = analyze_frame(
        frame,
        source=record["filename"],
        apply=True,
        target=record["declared_target"],
    )
    cleaned_csv = None if cleaned is None else cleaned.to_csv(index=False)
    record["applied"] = True
    record["summary"] = report["summary"]
    record["report"] = report
    record["cleaned_csv"] = cleaned_csv
    store.update(record)
    return {
        "dataset_id": record["dataset_id"],
        "applied": True,
        "summary": record["summary"],
        "report_url": f"/datasets/{dataset_id}",
        "cleaned_url": f"/datasets/{dataset_id}/cleaned",
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
    record = {
        "dataset_id": dataset_id,
        "filename": filename,
        "created_at": created_at,
        "rows": int(frame.shape[0]),
        "columns": int(frame.shape[1]),
        "applied": cleaned is not None,
        "summary": report["summary"],
        "report": report,
        "cleaned_csv": cleaned_csv,
        "frame": frame,
        "declared_target": declared_target,
    }
    store.add(record)
    return {
        "dataset_id": record["dataset_id"],
        "filename": record["filename"],
        "created_at": record["created_at"],
        "rows": record["rows"],
        "columns": record["columns"],
        "applied": record["applied"],
        "summary": record["summary"],
        "report_url": f"/datasets/{dataset_id}",
        "review_url": f"/datasets/{dataset_id}/review",
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

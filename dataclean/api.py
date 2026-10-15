"""API FastAPI con aislamiento de informes por usuario."""

from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from dataclean.cli import analyze_frame
from dataclean.plan import apply_plan
from dataclean.report import render_report_html
from dataclean.store import DatasetStore

app = FastAPI(
    title="DataClean AI",
    description="Perfil, calidad, plan de limpieza, modelado, exportación HTML y descarga del CSV limpio. Informes aislados por usuario.",
    version="0.10.0",
)
store = DatasetStore()


def get_user_id(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> str:
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(status_code=401, detail="Cabecera X-User-Id requerida")
    return x_user_id.strip()


@app.post("/datasets", status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    user_id: str = Depends(get_user_id),
) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Se espera un archivo CSV")
    content = await file.read()
    try:
        df = pd.read_csv(pd.io.common.BytesIO(content))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"CSV inválido: {exc}") from exc
    report, _ = analyze_frame(df, source=file.filename)
    record = store.create(user_id, file.filename, df, report)
    return {
        "dataset_id": record["dataset_id"],
        "filename": record["filename"],
        "summary": record["summary"],
        "html_url": f"/datasets/{record['dataset_id']}/report.html",
    }


@app.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    return record


@app.post("/datasets/{dataset_id}/accept")
def accept_plan(dataset_id: str, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    if record.get("applied"):
        return {"dataset_id": dataset_id, "applied": True, "message": "El plan ya estaba aplicado"}
    folder = store._user_dir(user_id) / dataset_id
    df = pd.read_csv(folder / "original.csv")
    plan = record["report"].get("plan") or []
    cleaned = apply_plan(df, plan)
    record["applied"] = True
    record["report"]["applied"] = True
    store.update(user_id, dataset_id, record, cleaned)
    return {"dataset_id": dataset_id, "applied": True, "rows": len(cleaned)}


@app.get("/datasets/{dataset_id}/report.html", response_class=HTMLResponse)
def report_html(dataset_id: str, user_id: str = Depends(get_user_id)) -> str:
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    return render_report_html(record)


@app.get("/datasets/{dataset_id}/cleaned.csv")
def download_cleaned(dataset_id: str, user_id: str = Depends(get_user_id)) -> FileResponse:
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    if not record.get("applied"):
        raise HTTPException(status_code=400, detail="El plan aún no ha sido aplicado")
    folder = store._user_dir(user_id) / dataset_id
    cleaned_path = folder / "cleaned.csv"
    if not cleaned_path.exists():
        raise HTTPException(status_code=404, detail="Archivo limpio no encontrado")
    return FileResponse(
        cleaned_path,
        media_type="text/csv",
        filename=f"{dataset_id}_cleaned.csv",
    )

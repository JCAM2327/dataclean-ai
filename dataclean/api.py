"""API FastAPI con aislamiento de informes por usuario, autenticación opcional por API key y documentación OpenAPI enriquecida."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from dataclean.cli import analyze_frame
from dataclean.io import SUPPORTED_EXTENSIONS, load_dataframe
from dataclean.plan import apply_plan
from dataclean.report import render_report_html
from dataclean.store import DatasetStore

app = FastAPI(
    title="DataClean AI",
    description=(
        "Plataforma para perfilar datasets tabulares, detectar problemas de calidad, "
        "generar y aplicar planes de limpieza (incluye clipping de outliers IQR), detectar variable objetivo y comparar modelos baseline. "
        "Soporta carga de CSV, Excel (.xlsx/.xls) y Parquet. "
        "Los informes se aíslan por usuario mediante la cabecera obligatoria `X-User-Id`. "
        "Si se configura la variable de entorno `DATACLEAN_API_KEY`, se exige adicionalmente la cabecera `X-API-Key`."
    ),
    version="0.14.0",
    openapi_tags=[
        {"name": "Datasets", "description": "Carga, consulta y gestión de datasets y sus informes."},
        {"name": "Informes", "description": "Exportación de informes HTML y descarga de datos limpios."},
    ],
)
store = DatasetStore()


def get_user_id(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str:
    expected_key = os.environ.get("DATACLEAN_API_KEY")
    if expected_key and (not x_api_key or x_api_key != expected_key):
        raise HTTPException(status_code=401, detail="Cabecera X-API-Key requerida o inválida")
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(status_code=401, detail="Cabecera X-User-Id requerida")
    return x_user_id.strip()


class Summary(BaseModel):
    issue_count: int = Field(..., description="Cantidad de issues de calidad detectados")
    high_or_critical: int = Field(..., description="Issues de severidad alta o crítica")
    plan_steps: int = Field(..., description="Número de pasos del plan de limpieza")
    ready_for_modeling: bool = Field(..., description="Si el dataset está listo para modelado")
    target_column: str | None = Field(None, description="Columna objetivo detectada")
    target_task: str | None = Field(None, description="Tipo de tarea (classification/regression)")
    model_status: str | None = Field(None, description="Estado de la comparación de modelos")
    model_winner: str | None = Field(None, description="Modelo ganador según métricas")


class UploadResponse(BaseModel):
    dataset_id: str = Field(..., description="Identificador único del dataset")
    filename: str = Field(..., description="Nombre del archivo original")
    summary: Summary
    html_url: str = Field(..., description="Ruta relativa al informe HTML")


class AcceptResponse(BaseModel):
    dataset_id: str
    applied: bool = Field(..., description="Indica si el plan quedó aplicado")
    rows: int | None = Field(None, description="Número de filas del CSV limpio")
    message: str | None = Field(None, description="Mensaje informativo opcional")


@app.post(
    "/datasets",
    status_code=201,
    tags=["Datasets"],
    summary="Cargar dataset tabular",
    description="Sube un archivo CSV, Excel (.xlsx/.xls) o Parquet, genera el informe de perfil/calidad/plan/modelado y lo persiste aislado por usuario.",
    response_model=UploadResponse,
    responses={
        400: {"description": "Archivo inválido o formato no soportado"},
        401: {"description": "Cabecera X-User-Id ausente o vacía, o X-API-Key requerida/inválida"},
    },
)
async def upload_dataset(
    file: UploadFile = File(..., description="Archivo tabular (CSV, Excel, Parquet) a analizar"),
    user_id: str = Depends(get_user_id),
) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo requerido")
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado: {ext}. Soportados: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )
    content = await file.read()
    try:
        df = load_dataframe(content, filename=file.filename)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Archivo inválido: {exc}") from exc
    report, _ = analyze_frame(df, source=file.filename)
    record = store.create(user_id, file.filename, df, report)
    return UploadResponse(
        dataset_id=record["dataset_id"],
        filename=record["filename"],
        summary=Summary(**record["summary"]),
        html_url=f"/datasets/{record['dataset_id']}/report.html",
    )


@app.get(
    "/datasets/{dataset_id}",
    tags=["Datasets"],
    summary="Consultar dataset",
    description="Recupera el registro completo del dataset (informe, plan, estado) perteneciente al usuario.",
    responses={404: {"description": "Dataset no encontrado o no pertenece al usuario"}},
)
def get_dataset(dataset_id: str, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    return record


@app.post(
    "/datasets/{dataset_id}/accept",
    tags=["Datasets"],
    summary="Aceptar plan de limpieza",
    description="Aplica el plan de limpieza generado, persiste el CSV limpio y marca el dataset como aplicado.",
    response_model=AcceptResponse,
    responses={404: {"description": "Dataset no encontrado"}},
)
def accept_plan(dataset_id: str, user_id: str = Depends(get_user_id)) -> AcceptResponse:
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    if record.get("applied"):
        return AcceptResponse(
            dataset_id=dataset_id,
            applied=True,
            message="El plan ya estaba aplicado",
        )
    folder = store._user_dir(user_id) / dataset_id
    df = pd.read_csv(folder / "original.csv")
    plan = record["report"].get("plan") or []
    cleaned = apply_plan(df, plan)
    record["applied"] = True
    record["report"]["applied"] = True
    store.update(user_id, dataset_id, record, cleaned)
    return AcceptResponse(dataset_id=dataset_id, applied=True, rows=len(cleaned))


@app.get(
    "/datasets/{dataset_id}/report.html",
    response_class=HTMLResponse,
    tags=["Informes"],
    summary="Informe HTML",
    description="Devuelve un documento HTML autocontenido con el perfil, issues, plan, objetivo y comparación de modelos.",
    responses={404: {"description": "Dataset no encontrado"}},
)
def report_html(dataset_id: str, user_id: str = Depends(get_user_id)) -> str:
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    return render_report_html(record)


@app.get(
    "/datasets/{dataset_id}/cleaned.csv",
    tags=["Informes"],
    summary="Descargar CSV limpio",
    description="Descarga el archivo CSV resultante tras aplicar el plan de limpieza. Requiere que el plan haya sido aceptado.",
    responses={
        400: {"description": "El plan aún no ha sido aplicado"},
        404: {"description": "Dataset o archivo limpio no encontrado"},
    },
)
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


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    openapi_schema["info"]["x-logo"] = {"url": "https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png"}
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
"""API FastAPI de DataClean AI con documentación OpenAPI enriquecida."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from dataclean import __version__
from dataclean.cli import analyze_frame
from dataclean.io import load_dataframe
from dataclean.report import render_report_html
from dataclean.store import DatasetStore

app = FastAPI(
    title="DataClean AI",
    description=(
        "Plataforma para perfilar datasets tabulares, detectar problemas de calidad, "
        "generar y aplicar planes de limpieza, detectar variable objetivo, comparar modelos "
        "baseline e informar importancia de variables. Incluye asesor de estrategias de "
        "modelado con evaluación de clustering (KMeans) y estabilidad bootstrap."
    ),
    version=__version__,
    openapi_tags=[
        {"name": "Datasets", "description": "Carga, consulta y gestión de datasets y sus informes."},
        {"name": "Informes", "description": "Exportación de informes HTML y descarga de datos."},
        {"name": "Sistema", "description": "Estado del servicio y configuración operativa."},
    ],
)

CORS_ORIGINS = os.getenv("DATACLEAN_CORS_ORIGINS", "*").split(",")
API_KEY = os.getenv("DATACLEAN_API_KEY")
STORE_ROOT = Path(os.getenv("DATACLEAN_STORE_ROOT", "data"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = DatasetStore(STORE_ROOT)


def get_user_id(user_id: str = Query("anonymous", description="Identificador del usuario para aislamiento de datos.")) -> str:
    return user_id


@app.get("/health", tags=["Sistema"], summary="Estado del servicio")
def health() -> dict[str, str]:
    """Devuelve el estado operativo y la versión actual."""
    return {"status": "ok", "version": __version__}


@app.post("/datasets", status_code=201, tags=["Datasets"], summary="Cargar y analizar un dataset")
async def upload_dataset(
    file: UploadFile = File(..., description="Archivo tabular (CSV, Excel o Parquet)."),
    target: str | None = Query(None, description="Nombre de la columna objetivo. Si se omite, se infiere."),
    bootstrap_resamples: int = Query(20, ge=1, le=100, description="Número de remuestreos bootstrap para el asesor."),
    user_id: str = Depends(get_user_id),
) -> dict[str, Any]:
    """Carga un dataset, ejecuta el análisis completo (perfil, calidad, plan, modelos, asesor) y lo persiste.

    Retorna el identificador del dataset y un resumen del informe.
    """
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Archivo vacío.")
    try:
        # Escribir temporalmente para load_dataframe
        tmp = Path("/tmp") / (file.filename or "upload.csv")
        tmp.write_bytes(content)
        df = load_dataframe(str(tmp))
        tmp.unlink(missing_ok=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo cargar el archivo: {exc}") from exc

    report, _ = analyze_frame(
        df,
        source=file.filename or "upload",
        bootstrap_resamples=bootstrap_resamples,
        target=target,
    )
    record = store.create(user_id, file.filename or "upload.csv", df, report, content)
    return {
        "dataset_id": record["dataset_id"],
        "summary": record["summary"],
        "advisor": report.get("advisor"),
    }


@app.get("/datasets/{dataset_id}", tags=["Datasets"], summary="Obtener informe de un dataset")
def get_dataset(dataset_id: str, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    """Recupera el registro completo del dataset, incluyendo el informe de análisis."""
    record = store.get(user_id, dataset_id)
    if not record:
        raise HTTPException(status_code=404, detail="Dataset no encontrado.")
    return record


@app.get("/datasets/{dataset_id}/report.html", tags=["Informes"], summary="Informe HTML del dataset", response_class=HTMLResponse)
def get_report_html(dataset_id: str, user_id: str = Depends(get_user_id)) -> str:
    """Genera y devuelve el informe HTML autocontenido del dataset."""
    record = store.get(user_id, dataset_id)
    if not record:
        raise HTTPException(status_code=404, detail="Dataset no encontrado.")
    return render_report_html(record)

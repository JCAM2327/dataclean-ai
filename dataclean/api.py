"""API FastAPI con aislamiento de informes por usuario, autenticación opcional por API key y documentación OpenAPI enriquecida."""

from __future__ import annotations

import io
import os
import time
from pathlib import Path
from typing import Any, Literal

import pandas as pd
from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

from dataclean.advisor import suggest_modeling_strategy
from dataclean.cli import analyze_frame
from dataclean.eda import run_eda
from dataclean.io import SUPPORTED_EXTENSIONS, load_dataframe
from dataclean.plan import apply_plan
from dataclean.profile import profile_dataframe
from dataclean.report import render_report_html
from dataclean.store import DatasetStore
from dataclean.validation import assess_quality, suggest_rules

app = FastAPI(
    title="DataClean AI",
    description=(
        "Plataforma para perfilar datasets tabulares, detectar problemas de calidad, "
        "generar y aplicar planes de limpieza, detectar variable objetivo, comparar modelos baseline e informar importancia de variables. "
        "Incluye asesor de estrategias de modelado con evaluación mínima de clustering (y exposición de etiquetas), persistido en el registro del dataset, "
        "y descarga del CSV limpio con columna opcional de etiquetas de cluster."
    ),
    version="0.35.0",
    openapi_tags=[
        {"name": "Datasets", "description": "Carga, consulta y gestión de datasets y sus informes."},
        {"name": "Informes", "description": "Exportación de informes HTML y descarga de datos limpios."},
        {"name": "Sistema", "description": "Estado del servicio y configuración operativa."},
    ],
)

CORS_ORIGINS = os.getenv("DATACLEAN_CORS_ORIGINS", "*").split(",")
MAX_AGE_HOURS = float(os.getenv("DATACLEAN_MAX_AGE_HOURS", 24))
CLEANUP_INTERVAL = int(os.getenv("DATACLEAN_CLEANUP_INTERVAL_SECONDS", 3600))
API_KEY = os.getenv("DATACLEAN_API_KEY")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = DatasetStore()
last_cleanup = 0.0


def _maybe_cleanup() -> None:
    global last_cleanup
    now = time.time()
    if now - last_cleanup > CLEANUP_INTERVAL:
        store.cleanup_expired(MAX_AGE_HOURS)
        last_cleanup = now


async def get_user_id(
    x_user_id: str = Header(..., alias="X-User-Id"),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> str:
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="API key inválida")
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(status_code=400, detail="X-User-Id obligatorio")
    return x_user_id.strip()


class ValidateRequest(BaseModel):
    rules: list[dict[str, Any]] | None = None


@app.get("/health", tags=["Sistema"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.35.0"}


@app.post("/datasets", status_code=201, tags=["Datasets"])
async def upload_dataset(
    file: UploadFile = File(...),
    target: str | None = Query(None),
    scale_numeric: bool = Query(False),
    encode_categorical: Literal["onehot", "ordinal"] | None = Query(None),
    onehot_drop_first: bool = Query(False),
    drop_low_variance_threshold: float | None = Query(None),
    drop_high_correlation_threshold: float | None = Query(None),
    importance_threshold: float | None = Query(None),
    drop_low_importance: bool = Query(False),
    user_id: str = Depends(get_user_id),
) -> dict[str, Any]:
    _maybe_cleanup()
    content = await file.read()
    max_bytes = int(os.getenv("DATACLEAN_MAX_UPLOAD_BYTES", 50 * 1024 * 1024))
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="Archivo demasiado grande")
    filename = file.filename or "upload.csv"
    try:
        tmp = Path("/tmp") / f"upload_{user_id}_{filename}"
        tmp.write_bytes(content)
        df = load_dataframe(tmp)
        tmp.unlink(missing_ok=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo cargar el archivo: {exc}") from exc

    report, _ = analyze_frame(
        df,
        source=filename,
        target=target,
        scale_numeric=scale_numeric,
        encode_categorical=encode_categorical,
        onehot_drop_first=onehot_drop_first,
        drop_low_variance_threshold=drop_low_variance_threshold,
        drop_high_correlation_threshold=drop_high_correlation_threshold,
        importance_threshold=importance_threshold,
        drop_low_importance=drop_low_importance,
    )
    record = store.create(user_id, filename, df, report, content=content)
    try:
        advice = suggest_modeling_strategy(
            df,
            report.get("target"),
            report.get("modeling"),
        )
        record["advisor"] = advice
        store.update(user_id, record["dataset_id"], record)
    except Exception:
        pass
    return record


@app.get("/datasets", tags=["Datasets"])
def list_datasets(user_id: str = Depends(get_user_id)) -> list[dict[str, Any]]:
    _maybe_cleanup()
    return store.list_for_user(user_id)


@app.get("/datasets/{dataset_id}", tags=["Datasets"])
def get_dataset(dataset_id: str, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    return record


@app.delete("/datasets/{dataset_id}", status_code=204, tags=["Datasets"])
def delete_dataset(dataset_id: str, user_id: str = Depends(get_user_id)) -> None:
    if not store.delete(user_id, dataset_id):
        raise HTTPException(status_code=404, detail="Dataset no encontrado")


@app.get("/datasets/{dataset_id}/preview", tags=["Datasets"])
def preview_dataset(
    dataset_id: str,
    user_id: str = Depends(get_user_id),
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    try:
        if record.get("applied"):
            folder = store.dataset_dir(user_id, dataset_id)
            cleaned_parquet = folder / "cleaned.parquet"
            cleaned_csv = folder / "cleaned.csv"
            if cleaned_parquet.exists() and cleaned_parquet.stat().st_size > 0:
                df = pd.read_parquet(cleaned_parquet)
            elif cleaned_csv.exists():
                df = pd.read_csv(cleaned_csv)
            else:
                raise FileNotFoundError("No cleaned data")
            source = "cleaned"
        else:
            df = store.load_original(user_id, dataset_id)
            source = "original"
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    preview = df.head(limit).to_dict(orient="records")
    return {
        "dataset_id": dataset_id,
        "source": source,
        "returned_rows": len(preview),
        "columns": list(df.columns),
        "preview": preview,
    }


@app.post("/datasets/{dataset_id}/accept", tags=["Datasets"])
def accept_plan(dataset_id: str, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    if record.get("applied"):
        return record
    try:
        df = store.load_original(user_id, dataset_id)
        plan = record["report"].get("plan") or []
        cleaned = apply_plan(df, plan)
        record["applied"] = True
        try:
            advice = suggest_modeling_strategy(
                cleaned,
                record["report"].get("target"),
                record["report"].get("modeling"),
            )
            record["advisor"] = advice
        except Exception:
            pass
        store.update(user_id, dataset_id, record, cleaned=cleaned)
        return record
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/datasets/{dataset_id}/importances", tags=["Informes"])
def get_importances(dataset_id: str, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    modeling = record["report"].get("modeling") or {}
    models = []
    for m in modeling.get("models") or []:
        if m.get("feature_importances"):
            models.append({
                "name": m.get("name"),
                "feature_importances": m.get("feature_importances"),
            })
    return {
        "dataset_id": dataset_id,
        "models": models,
        "aggregated_importances": modeling.get("aggregated_importances") or [],
    }


@app.get("/datasets/{dataset_id}/eda", tags=["Datasets"])
def get_eda(dataset_id: str, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    try:
        df = store.load_original(user_id, dataset_id)
        eda = run_eda(df)
        eda["dataset_id"] = dataset_id
        return eda
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/datasets/{dataset_id}/validation/suggestions", tags=["Datasets"])
def get_validation_suggestions(dataset_id: str, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    try:
        df = store.load_original(user_id, dataset_id)
        rules = suggest_rules(df)
        return {"dataset_id": dataset_id, "rules": rules}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/datasets/{dataset_id}/validate", tags=["Datasets"])
def validate_dataset(
    dataset_id: str,
    body: ValidateRequest | None = None,
    user_id: str = Depends(get_user_id),
) -> dict[str, Any]:
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    try:
        df = store.load_original(user_id, dataset_id)
        if body and body.rules:
            rules = []
            for i, rule in enumerate(body.rules):
                r = dict(rule)
                if "id" not in r:
                    r["id"] = f"user-{i}"
                rules.append(r)
        else:
            rules = suggest_rules(df)
        assessment = assess_quality(df, rules)
        assessment["dataset_id"] = dataset_id
        return assessment
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/datasets/{dataset_id}/advisor", tags=["Informes"])
def get_advisor(dataset_id: str, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    """Devuelve la recomendación del asesor de modelado y, si es viable, una evaluación mínima de clustering."""
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    if record.get("advisor"):
        advice = dict(record["advisor"])
        advice["dataset_id"] = dataset_id
        return advice
    try:
        if record.get("applied"):
            folder = store.dataset_dir(user_id, dataset_id)
            cleaned_parquet = folder / "cleaned.parquet"
            cleaned_csv = folder / "cleaned.csv"
            if cleaned_parquet.exists() and cleaned_parquet.stat().st_size > 0:
                df = pd.read_parquet(cleaned_parquet)
            elif cleaned_csv.exists():
                df = pd.read_csv(cleaned_csv)
            else:
                raise FileNotFoundError("No cleaned data")
        else:
            df = store.load_original(user_id, dataset_id)
        target_report = record["report"].get("target")
        model_report = record["report"].get("modeling")
        advice = suggest_modeling_strategy(df, target_report, model_report)
        advice["dataset_id"] = dataset_id
        record["advisor"] = advice
        store.update(user_id, dataset_id, record)
        return advice
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/datasets/{dataset_id}/clusters", tags=["Informes"])
def get_clusters(dataset_id: str, user_id: str = Depends(get_user_id)) -> dict[str, Any]:
    """Devuelve las etiquetas de clustering del mejor k cuando están disponibles en el asesor persistido."""
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    advisor = record.get("advisor") or {}
    cr = advisor.get("clustering_results") or {}
    labels = cr.get("labels")
    if labels is None:
        raise HTTPException(status_code=404, detail="Etiquetas de clustering no disponibles")
    return {
        "dataset_id": dataset_id,
        "best_k": cr.get("best_k"),
        "best_silhouette": cr.get("best_silhouette"),
        "n_samples": cr.get("n_samples"),
        "labels": labels,
    }


@app.get("/datasets/{dataset_id}/download", tags=["Informes"])
def download_cleaned(
    dataset_id: str,
    user_id: str = Depends(get_user_id),
    include_clusters: bool = Query(False, description="Incluir columna 'cluster' si las etiquetas están disponibles y coinciden en longitud"),
):
    """Descarga el dataset limpio en formato CSV. Opcionalmente añade la columna de etiquetas de cluster."""
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    if not record.get("applied"):
        raise HTTPException(status_code=400, detail="El plan de limpieza no ha sido aceptado")
    folder = store.dataset_dir(user_id, dataset_id)
    cleaned_parquet = folder / "cleaned.parquet"
    cleaned_csv = folder / "cleaned.csv"
    try:
        if cleaned_parquet.exists() and cleaned_parquet.stat().st_size > 0:
            df = pd.read_parquet(cleaned_parquet)
        elif cleaned_csv.exists():
            df = pd.read_csv(cleaned_csv)
        else:
            raise FileNotFoundError("No cleaned data")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if include_clusters:
        advisor = record.get("advisor") or {}
        cr = advisor.get("clustering_results") or {}
        labels = cr.get("labels")
        if labels is not None and len(labels) == len(df):
            df = df.copy()
            df["cluster"] = labels

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=cleaned_{dataset_id}.csv"},
    )


@app.get("/datasets/{dataset_id}/report.html", response_class=HTMLResponse, tags=["Informes"])
def get_report_html(dataset_id: str, user_id: str = Depends(get_user_id)) -> HTMLResponse:
    record = store.get(user_id, dataset_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Dataset no encontrado")
    if not record.get("advisor"):
        try:
            if record.get("applied"):
                folder = store.dataset_dir(user_id, dataset_id)
                cleaned_parquet = folder / "cleaned.parquet"
                cleaned_csv = folder / "cleaned.csv"
                if cleaned_parquet.exists() and cleaned_parquet.stat().st_size > 0:
                    df = pd.read_parquet(cleaned_parquet)
                elif cleaned_csv.exists():
                    df = pd.read_csv(cleaned_csv)
                else:
                    raise FileNotFoundError("No cleaned data")
            else:
                df = store.load_original(user_id, dataset_id)
            target_report = record["report"].get("target")
            model_report = record["report"].get("modeling")
            advice = suggest_modeling_strategy(df, target_report, model_report)
            record = dict(record)
            record["advisor"] = advice
            store.update(user_id, dataset_id, record)
        except Exception:
            pass
    html = render_report_html(record)
    return HTMLResponse(content=html)


def custom_openapi() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

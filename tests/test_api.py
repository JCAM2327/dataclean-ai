"""Pruebas de contrato de la API con aislamiento por usuario."""

from __future__ import annotations

import io

import pandas as pd
from fastapi.testclient import TestClient

from dataclean.api import app

client = TestClient(app)


def _csv_bytes() -> bytes:
    df = pd.DataFrame(
        {
            "edad": [30, 40, None, 50],
            "ciudad": ["A", "B", "A", "C"],
            "objetivo": [0, 1, 0, 1],
        }
    )
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def test_upload_requires_user_header():
    response = client.post("/datasets", files={"file": ("sample.csv", _csv_bytes(), "text/csv")})
    assert response.status_code == 401


def test_upload_and_isolation():
    headers = {"X-User-Id": "user-a"}
    response = client.post(
        "/datasets",
        files={"file": ("sample.csv", _csv_bytes(), "text/csv")},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    dataset_id = body["dataset_id"]
    assert "html_url" in body
    assert body["summary"]["issue_count"] >= 0

    # Propietario puede leer
    get_own = client.get(f"/datasets/{dataset_id}", headers=headers)
    assert get_own.status_code == 200
    assert get_own.json()["dataset_id"] == dataset_id

    # Otro usuario no puede
    other = client.get(f"/datasets/{dataset_id}", headers={"X-User-Id": "user-b"})
    assert other.status_code == 404

    # HTML del propietario
    html = client.get(f"/datasets/{dataset_id}/report.html", headers=headers)
    assert html.status_code == 200
    assert "text/html" in html.headers["content-type"]
    assert "Informe" in html.text

    # HTML de otro usuario
    html_other = client.get(f"/datasets/{dataset_id}/report.html", headers={"X-User-Id": "user-b"})
    assert html_other.status_code == 404


def test_accept_plan_scoped():
    headers = {"X-User-Id": "user-c"}
    response = client.post(
        "/datasets",
        files={"file": ("sample.csv", _csv_bytes(), "text/csv")},
        headers=headers,
    )
    dataset_id = response.json()["dataset_id"]
    accept = client.post(f"/datasets/{dataset_id}/accept", headers=headers)
    assert accept.status_code == 200
    assert accept.json()["applied"] is True

    # Otro usuario no puede aceptar
    other_accept = client.post(f"/datasets/{dataset_id}/accept", headers={"X-User-Id": "user-d"})
    assert other_accept.status_code == 404


def test_download_cleaned_csv():
    headers = {"X-User-Id": "user-e"}
    response = client.post(
        "/datasets",
        files={"file": ("sample.csv", _csv_bytes(), "text/csv")},
        headers=headers,
    )
    dataset_id = response.json()["dataset_id"]

    # Antes de aceptar no se puede descargar
    before = client.get(f"/datasets/{dataset_id}/cleaned.csv", headers=headers)
    assert before.status_code == 400

    # Aceptar plan
    client.post(f"/datasets/{dataset_id}/accept", headers=headers)

    # Propietario puede descargar
    download = client.get(f"/datasets/{dataset_id}/cleaned.csv", headers=headers)
    assert download.status_code == 200
    assert "text/csv" in download.headers["content-type"]
    assert "edad" in download.text

    # Otro usuario no puede
    other = client.get(f"/datasets/{dataset_id}/cleaned.csv", headers={"X-User-Id": "user-f"})
    assert other.status_code == 404

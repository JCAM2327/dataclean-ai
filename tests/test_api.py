"""Pruebas básicas de la API FastAPI."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dataclean.api import app


@pytest.fixture
def client(tmp_path: Path):
    # Aislar el almacén
    import os
    os.environ["DATACLEAN_STORE_ROOT"] = str(tmp_path / "store")
    # Recargar store si es necesario, pero para simplicidad usamos el global
    from dataclean import api as api_mod
    api_mod.store = api_mod.DatasetStore(tmp_path / "store")
    return TestClient(app)


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_upload_and_get(client: TestClient, tmp_path: Path):
    csv = tmp_path / "sample.csv"
    csv.write_text("id,edad,objetivo\n1,30,1\n2,40,0\n3,35,1\n", encoding="utf-8")
    with csv.open("rb") as f:
        r = client.post(
            "/datasets",
            files={"file": ("sample.csv", f, "text/csv")},
            params={"user_id": "testuser", "bootstrap_resamples": 5},
        )
    assert r.status_code == 201
    data = r.json()
    assert "dataset_id" in data
    assert "summary" in data
    ds_id = data["dataset_id"]

    r2 = client.get(f"/datasets/{ds_id}", params={"user_id": "testuser"})
    assert r2.status_code == 200
    assert r2.json()["dataset_id"] == ds_id

    r3 = client.get(f"/datasets/{ds_id}/report.html", params={"user_id": "testuser"})
    assert r3.status_code == 200
    assert "Informe" in r3.text

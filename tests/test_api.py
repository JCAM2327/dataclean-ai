import pandas as pd
from fastapi.testclient import TestClient

from dataclean.api import app, store


CSV = """id,edad,ciudad,objetivo
1,34,MDQ,1
2,29,BA,0
3,41,BA,1
4,22,CBA,0
5,55,MDQ,1
6,38,MDQ,1
7,47,BA,0
8,33,CBA,0
"""


def setup_function() -> None:
    store.clear()


def test_upload_returns_report_and_can_be_retrieved():
    client = TestClient(app)
    response = client.post(
        "/datasets",
        files={"file": ("muestra.csv", CSV, "text/csv")},
        data={"target": "objetivo"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "muestra.csv"
    assert body["rows"] == 8
    assert body["columns"] == 4
    assert body["summary"]["target_column"] == "objetivo"
    assert body["summary"]["model_status"] in {"compared", "skipped"}

    fetched = client.get(body["report_url"])
    assert fetched.status_code == 200
    report = fetched.json()["report"]
    assert report["profile"]["rows"] == 8
    assert report["target"]["column"] == "objetivo"
    assert "modeling" in report

    listed = client.get("/datasets")
    assert listed.status_code == 200
    assert listed.json()["count"] == 1


def test_upload_apply_exposes_cleaned_csv():
    duplicated = CSV + "8,33,CBA,0\n"
    client = TestClient(app)
    response = client.post(
        "/datasets",
        files={"file": ("dup.csv", duplicated, "text/csv")},
        data={"apply": "true", "target": "objetivo"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["applied"] is True
    cleaned = client.get(f"/datasets/{body['dataset_id']}/cleaned")
    assert cleaned.status_code == 200
    frame = pd.read_csv(pd.io.common.StringIO(cleaned.text))
    assert frame.duplicated().sum() == 0
    assert "id" not in frame.columns


def test_rejects_empty_non_csv_and_unknown_id():
    client = TestClient(app)
    empty = client.post("/datasets", files={"file": ("vacio.csv", b"", "text/csv")})
    assert empty.status_code == 400

    wrong = client.post("/datasets", files={"file": ("notas.txt", b"a,b\n1,2\n", "text/plain")})
    assert wrong.status_code == 400

    broken = client.post(
        "/datasets",
        files={"file": ("roto.csv", b"a,b\n1,2,3\n", "text/csv")},
    )
    assert broken.status_code == 422

    missing = client.get("/datasets/no-existe")
    assert missing.status_code == 404


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

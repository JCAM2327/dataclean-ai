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
    assert "review_url" in body

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


def test_review_and_accept_plan():
    client = TestClient(app)
    response = client.post(
        "/datasets",
        files={"file": ("muestra.csv", CSV, "text/csv")},
        data={"target": "objetivo"},
    )
    assert response.status_code == 201
    dataset_id = response.json()["dataset_id"]
    assert response.json()["applied"] is False

    review = client.get(f"/datasets/{dataset_id}/review")
    assert review.status_code == 200
    body = review.json()
    assert body["applied"] is False
    assert isinstance(body["issues"], list)
    assert isinstance(body["plan"], list)
    assert len(body["plan"]) > 0

    accept = client.post(f"/datasets/{dataset_id}/accept")
    assert accept.status_code == 200
    assert accept.json()["applied"] is True

    cleaned = client.get(f"/datasets/{dataset_id}/cleaned")
    assert cleaned.status_code == 200
    frame = pd.read_csv(pd.io.common.StringIO(cleaned.text))
    assert "id" not in frame.columns

    second = client.post(f"/datasets/{dataset_id}/accept")
    assert second.status_code == 409


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

    missing_review = client.get("/datasets/no-existe/review")
    assert missing_review.status_code == 404

    missing_accept = client.post("/datasets/no-existe/accept")
    assert missing_accept.status_code == 404


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_persistence_survives_store_reload():
    """El informe y los datos originales permanecen tras reiniciar el almacén."""
    from pathlib import Path
    import tempfile
    from dataclean.api import DatasetStore

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "store"
        store_a = DatasetStore(root)
        # Simular carga mediante el almacén (sin pasar por la app global)
        from dataclean.cli import analyze_frame
        frame = pd.read_csv(pd.io.common.StringIO(CSV))
        report, _ = analyze_frame(frame, source="muestra.csv", apply=False, target="objetivo")
        dataset_id = "persist-test-id"
        record = {
            "dataset_id": dataset_id,
            "filename": "muestra.csv",
            "created_at": "2026-10-11T15:00:00+00:00",
            "rows": int(frame.shape[0]),
            "columns": int(frame.shape[1]),
            "applied": False,
            "summary": report["summary"],
            "report": report,
            "cleaned_csv": None,
            "frame": frame,
            "declared_target": "objetivo",
        }
        store_a.add(record)

        store_b = DatasetStore(root)
        loaded = store_b.get(dataset_id)
        assert loaded is not None
        assert loaded["rows"] == 8
        assert loaded["report"]["target"]["column"] == "objetivo"
        assert loaded["frame"].shape == (8, 4)
        assert store_b.list()[0]["dataset_id"] == dataset_id

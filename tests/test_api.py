"""Pruebas de la API FastAPI."""

from pathlib import Path

from fastapi.testclient import TestClient

from dataclean.api import app

client = TestClient(app)
SAMPLE = Path(__file__).parent.parent / "examples" / "sample.csv"
HEADERS = {"X-User-Id": "test-user"}


def _upload_sample() -> dict:
    with open(SAMPLE, "rb") as f:
        response = client.post(
            "/datasets",
            files={"file": ("sample.csv", f, "text/csv")},
            headers=HEADERS,
        )
    assert response.status_code == 201
    return response.json()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_upload_and_get_importances():
    data = _upload_sample()
    dataset_id = data["dataset_id"]
    assert "summary" in data

    imp_response = client.get(
        f"/datasets/{dataset_id}/importances",
        headers=HEADERS,
    )
    assert imp_response.status_code == 200
    imp = imp_response.json()
    assert imp["dataset_id"] == dataset_id
    assert "models" in imp
    assert len(imp["models"]) >= 1
    for model in imp["models"]:
        assert "feature_importances" in model
        assert isinstance(model["feature_importances"], list)
        assert len(model["feature_importances"]) > 0
    assert "aggregated_importances" in imp
    assert isinstance(imp["aggregated_importances"], list)
    if imp["aggregated_importances"]:
        assert all("feature" in a and "max_importance" in a for a in imp["aggregated_importances"])


def test_target_query_accept_and_preview():
    with open(SAMPLE, "rb") as f:
        response = client.post(
            "/datasets?target=objetivo",
            files={"file": ("sample.csv", f, "text/csv")},
            headers=HEADERS,
        )
    assert response.status_code == 201
    dataset_id = response.json()["dataset_id"]

    record = client.get(f"/datasets/{dataset_id}", headers=HEADERS).json()
    assert record["report"]["target"]["column"] == "objetivo"
    assert record["report"]["target"]["source"] == "explicit"

    preview = client.get(f"/datasets/{dataset_id}/preview", headers=HEADERS)
    assert preview.status_code == 200
    assert preview.json()["source"] == "original"
    assert preview.json()["returned_rows"] > 0

    accept = client.post(f"/datasets/{dataset_id}/accept", headers=HEADERS)
    assert accept.status_code == 200
    assert accept.json()["applied"] is True

    cleaned_preview = client.get(f"/datasets/{dataset_id}/preview", headers=HEADERS)
    assert cleaned_preview.status_code == 200
    assert cleaned_preview.json()["source"] == "cleaned"


def test_list_and_delete_dataset():
    data = _upload_sample()
    dataset_id = data["dataset_id"]

    listed = client.get("/datasets", headers=HEADERS)
    assert listed.status_code == 200
    assert dataset_id in {item["dataset_id"] for item in listed.json()}

    deleted = client.delete(f"/datasets/{dataset_id}", headers=HEADERS)
    assert deleted.status_code == 204
    assert client.get(f"/datasets/{dataset_id}", headers=HEADERS).status_code == 404


def test_eda_suggestions_and_validate():
    data = _upload_sample()
    dataset_id = data["dataset_id"]

    eda = client.get(f"/datasets/{dataset_id}/eda", headers=HEADERS)
    assert eda.status_code == 200
    body = eda.json()
    assert body["dataset_id"] == dataset_id
    assert body["rows"] > 0
    assert "numeric" in body and "recommendations" in body

    suggestions = client.get(
        f"/datasets/{dataset_id}/validation/suggestions", headers=HEADERS
    )
    assert suggestions.status_code == 200
    rules = suggestions.json()["rules"]
    assert any(rule["kind"] == "unique" and rule["column"] == "id" for rule in rules)

    validation = client.post(f"/datasets/{dataset_id}/validate", headers=HEADERS)
    assert validation.status_code == 200
    assessment = validation.json()
    assert 0 <= assessment["score"] <= 100
    assert len(assessment["dimensions"]) == 6

    custom = client.post(
        f"/datasets/{dataset_id}/validate",
        headers=HEADERS,
        json={"rules": [{"kind": "min", "column": "edad", "min": 18, "critical": True}]},
    )
    assert custom.status_code == 200
    results = custom.json()["results"]
    assert len(results) == 1
    assert results[0]["rule"]["id"] == "user-0"


def test_upload_limit(monkeypatch):
    monkeypatch.setenv("DATACLEAN_MAX_UPLOAD_BYTES", "10")
    response = client.post(
        "/datasets",
        files={"file": ("sample.csv", SAMPLE.read_bytes(), "text/csv")},
        headers=HEADERS,
    )
    assert response.status_code == 413


def test_advisor_endpoint():
    data = _upload_sample()
    dataset_id = data["dataset_id"]

    advisor = client.get(f"/datasets/{dataset_id}/advisor", headers=HEADERS)
    assert advisor.status_code == 200
    body = advisor.json()
    assert body["dataset_id"] == dataset_id
    assert "strategy" in body
    assert "recommendations" in body
    assert isinstance(body["recommendations"], list)
    assert "clustering_viable" in body
    assert body["strategy"] in {"supervised", "unsupervised", "insufficient"}

    # El asesor debe quedar persistido en el registro
    record = client.get(f"/datasets/{dataset_id}", headers=HEADERS).json()
    assert "advisor" in record
    assert record["advisor"]["strategy"] == body["strategy"]


def test_advisor_persisted_after_accept():
    data = _upload_sample()
    dataset_id = data["dataset_id"]

    accept = client.post(f"/datasets/{dataset_id}/accept", headers=HEADERS)
    assert accept.status_code == 200
    record = accept.json()
    assert record["applied"] is True
    assert "advisor" in record
    assert "strategy" in record["advisor"]


def test_clusters_endpoint_unavailable_for_small_sample():
    data = _upload_sample()
    dataset_id = data["dataset_id"]
    response = client.get(f"/datasets/{dataset_id}/clusters", headers=HEADERS)
    assert response.status_code == 404
    assert "no disponibles" in response.json()["detail"]

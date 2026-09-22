from __future__ import annotations

import uuid

from tests.conftest import make_pdf_bytes
from tests.mock_provider import MockVisionModelProvider


async def _upload_document(app_client) -> str:
    files = {"file": ("test.pdf", make_pdf_bytes(num_pages=2), "application/pdf")}
    response = await app_client.post("/api/documents/upload", files=files)
    return response.json()["id"]


def _extraction_payload(document_id: str) -> dict:
    return {
        "document_id": document_id,
        "fields": [
            {"name": "policy_number", "description": "Extract the policy number", "data_type": "String", "required": True},
            {"name": "patient_name", "description": "Full name of the patient", "data_type": "String", "required": True},
        ],
        "instructions": "Extract only information present in the document.",
    }


async def test_create_extraction_success(app_client):
    document_id = await _upload_document(app_client)
    response = await app_client.post("/api/extractions", json=_extraction_payload(document_id))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["fields_requested"] == 2
    assert body["fields_extracted"] == 2


async def test_get_extraction_result_contains_confidence_and_page(app_client):
    document_id = await _upload_document(app_client)
    create_response = await app_client.post("/api/extractions", json=_extraction_payload(document_id))
    extraction_id = create_response.json()["id"]

    response = await app_client.get(f"/api/extractions/{extraction_id}/result")
    assert response.status_code == 200
    body = response.json()
    assert len(body["results"]) == 2
    for item in body["results"]:
        assert item["confidence"] is not None
        assert item["page"] == 1


async def test_not_found_field_is_reported(app_client):
    document_id = await _upload_document(app_client)
    payload = _extraction_payload(document_id)
    payload["fields"].append(
        {"name": "missing_field", "description": "does not exist", "data_type": "String", "required": False}
    )

    from app.api import deps
    from app.main import app

    app.dependency_overrides[deps.get_provider] = lambda: MockVisionModelProvider(
        mode="success", field_values={"missing_field": {"value": None, "confidence": 0.0, "page": None, "evidence": None}}
    )
    try:
        create_response = await app_client.post("/api/extractions", json=payload)
        extraction_id = create_response.json()["id"]
        result = await app_client.get(f"/api/extractions/{extraction_id}/result")
        by_name = {r["name"]: r for r in result.json()["results"]}
        assert by_name["missing_field"]["status"] == "NOT_FOUND"
    finally:
        app.dependency_overrides.pop(deps.get_provider, None)


async def test_extraction_model_auth_error_returns_401_and_marks_failed(app_client):
    from app.api import deps
    from app.main import app

    document_id = await _upload_document(app_client)
    app.dependency_overrides[deps.get_provider] = lambda: MockVisionModelProvider(mode="auth_error")
    try:
        response = await app_client.post("/api/extractions", json=_extraction_payload(document_id))
        assert response.status_code == 401
    finally:
        app.dependency_overrides.pop(deps.get_provider, None)

    # The document itself should remain usable after a failed extraction attempt.
    doc_response = await app_client.get(f"/api/documents/{document_id}")
    assert doc_response.status_code == 200


async def test_extract_again_creates_new_run_without_overwriting(app_client):
    document_id = await _upload_document(app_client)
    payload = _extraction_payload(document_id)

    first = await app_client.post("/api/extractions", json=payload)
    second = await app_client.post("/api/extractions", json=payload)

    first_id = first.json()["id"]
    second_id = second.json()["id"]
    assert first_id != second_id

    first_get = await app_client.get(f"/api/extractions/{first_id}")
    second_get = await app_client.get(f"/api/extractions/{second_id}")
    assert first_get.status_code == 200
    assert second_get.status_code == 200


async def test_download_json(app_client):
    document_id = await _upload_document(app_client)
    create_response = await app_client.post("/api/extractions", json=_extraction_payload(document_id))
    extraction_id = create_response.json()["id"]

    response = await app_client.get(f"/api/extractions/{extraction_id}/download/json")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    body = response.json()
    assert len(body["fields"]) == 2


async def test_download_csv(app_client):
    document_id = await _upload_document(app_client)
    create_response = await app_client.post("/api/extractions", json=_extraction_payload(document_id))
    extraction_id = create_response.json()["id"]

    response = await app_client.get(f"/api/extractions/{extraction_id}/download/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Field" in response.text


async def test_get_nonexistent_extraction_returns_404(app_client):
    response = await app_client.get(f"/api/extractions/{uuid.uuid4()}")
    assert response.status_code == 404

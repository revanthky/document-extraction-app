from __future__ import annotations

import uuid

from tests.conftest import make_pdf_bytes


async def _upload(app_client, num_pages=2, filename="test.pdf"):
    files = {"file": (filename, make_pdf_bytes(num_pages=num_pages), "application/pdf")}
    return await app_client.post("/api/documents/upload", files=files)


async def test_upload_valid_pdf_returns_metadata(app_client):
    response = await _upload(app_client, num_pages=3)
    assert response.status_code == 200
    body = response.json()
    assert body["original_filename"] == "test.pdf"
    assert body["page_count"] == 3
    assert body["status"] == "UPLOADED"
    uuid.UUID(body["id"])  # valid UUID


async def test_upload_rejects_non_pdf(app_client):
    files = {"file": ("test.txt", b"hello world", "text/plain")}
    response = await app_client.post("/api/documents/upload", files=files)
    assert response.status_code == 415
    assert "Only PDF documents are supported" in response.json()["message"]


async def test_upload_rejects_corrupt_pdf(app_client):
    files = {"file": ("bad.pdf", b"not a real pdf", "application/pdf")}
    response = await app_client.post("/api/documents/upload", files=files)
    assert response.status_code == 422


async def test_get_document_after_upload(app_client):
    upload_response = await _upload(app_client)
    document_id = upload_response.json()["id"]
    response = await app_client.get(f"/api/documents/{document_id}")
    assert response.status_code == 200
    assert response.json()["id"] == document_id


async def test_get_nonexistent_document_returns_404(app_client):
    response = await app_client.get(f"/api/documents/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_get_document_page_returns_png(app_client):
    upload_response = await _upload(app_client, num_pages=2)
    document_id = upload_response.json()["id"]
    response = await app_client.get(f"/api/documents/{document_id}/pages/1")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


async def test_download_document_returns_original_pdf(app_client):
    upload_response = await _upload(app_client)
    document_id = upload_response.json()["id"]
    response = await app_client.get(f"/api/documents/{document_id}/download")
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")


async def test_delete_document_removes_it(app_client):
    upload_response = await _upload(app_client)
    document_id = upload_response.json()["id"]
    delete_response = await app_client.delete(f"/api/documents/{document_id}")
    assert delete_response.status_code == 200
    get_response = await app_client.get(f"/api/documents/{document_id}")
    assert get_response.status_code == 404

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.models import Document, Extraction, ExtractionField, ExtractionResult
from app.storage.minio_storage import MinIOObjectStorage
from tests.conftest import TEST_DATABASE_URL, TEST_MINIO_BUCKET, make_pdf_bytes


async def test_full_persistence_lifecycle_survives_simulated_restart(app_client, storage):
    # 1. Upload a PDF.
    files = {"file": ("policy.pdf", make_pdf_bytes(num_pages=2), "application/pdf")}
    upload_response = await app_client.post("/api/documents/upload", files=files)
    assert upload_response.status_code == 200
    document_id = upload_response.json()["id"]

    # 2. Verify the original PDF exists in MinIO.
    object_key = f"documents/{document_id}/original.pdf"
    assert storage.exists(TEST_MINIO_BUCKET, object_key) is True

    # 3. Verify document metadata exists in PostgreSQL.
    doc_response = await app_client.get(f"/api/documents/{document_id}")
    assert doc_response.status_code == 200
    assert doc_response.json()["page_count"] == 2

    # 4. Run extraction.
    payload = {
        "document_id": document_id,
        "fields": [
            {"name": "policy_number", "description": "Extract the policy number", "data_type": "String", "required": True}
        ],
        "instructions": "",
    }
    extraction_response = await app_client.post("/api/extractions", json=payload)
    assert extraction_response.status_code == 200
    extraction_id = extraction_response.json()["id"]

    # 5. Verify extraction, field definitions, and results exist in PostgreSQL.
    engine = create_async_engine(TEST_DATABASE_URL)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        extraction = await session.get(Extraction, uuid.UUID(extraction_id))
        assert extraction is not None
        assert extraction.status == "COMPLETED"

        fields = (
            await session.execute(
                select(ExtractionField).where(ExtractionField.extraction_id == extraction.id)
            )
        ).scalars().all()
        assert len(fields) == 1

        results = (
            await session.execute(
                select(ExtractionResult).where(ExtractionResult.extraction_id == extraction.id)
            )
        ).scalars().all()
        assert len(results) == 1
        assert results[0].confidence is not None
        assert results[0].page == 1
    await engine.dispose()

    # 6. "Restart the backend" -- create entirely fresh engine/session and storage
    # client instances, independent of anything cached in process memory, to prove
    # persistence rather than in-memory state.
    restart_engine = create_async_engine(TEST_DATABASE_URL)
    restart_session_factory = async_sessionmaker(bind=restart_engine, expire_on_commit=False)
    restart_storage = MinIOObjectStorage(
        endpoint="localhost:9000", access_key="minioadmin", secret_key="minioadmin", secure=False
    )

    # 7. Retrieve the document and results again.
    async with restart_session_factory() as session:
        document = await session.get(Document, uuid.UUID(document_id))
        assert document is not None
        assert document.status == "UPLOADED"

    # 8. Verify the PDF remains available from MinIO and structured data remains available.
    assert restart_storage.exists(TEST_MINIO_BUCKET, object_key) is True
    downloaded = restart_storage.download(TEST_MINIO_BUCKET, object_key)
    assert downloaded.startswith(b"%PDF")

    result_response = await app_client.get(f"/api/extractions/{extraction_id}/result")
    assert result_response.status_code == 200
    assert result_response.json()["results"][0]["value"] is not None

    await restart_engine.dispose()

    # 9. Run Extract Again and verify a new extraction run is created without
    # overwriting the previous run.
    second_response = await app_client.post("/api/extractions", json=payload)
    assert second_response.status_code == 200
    second_extraction_id = second_response.json()["id"]
    assert second_extraction_id != extraction_id

    original_still_present = await app_client.get(f"/api/extractions/{extraction_id}")
    assert original_still_present.status_code == 200

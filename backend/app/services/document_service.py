from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DocumentNotFoundError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.core.logging import get_logger
from app.db.models import Document, DocumentStatus
from app.pdf import service as pdf_service
from app.storage.base import ObjectStorage

logger = get_logger(__name__)

PDF_MIME_TYPE = "application/pdf"


def _object_key(document_id: uuid.UUID) -> str:
    return f"documents/{document_id}/original.pdf"


async def upload_document(
    db: AsyncSession,
    storage: ObjectStorage,
    bucket: str,
    *,
    filename: str,
    mime_type: str,
    data: bytes,
    max_size_bytes: int,
) -> Document:
    if mime_type != PDF_MIME_TYPE:
        raise UnsupportedFileTypeError("Only PDF documents are supported.")
    if len(data) > max_size_bytes:
        raise FileTooLargeError(
            f"File exceeds the maximum allowed size of {max_size_bytes // (1024 * 1024)} MB."
        )

    pdf_service.validate_pdf(data)
    page_count = pdf_service.get_page_count(data)

    document_id = uuid.uuid4()
    object_key = _object_key(document_id)

    # MinIO first: never create a document record for an object that failed to upload.
    storage.upload(bucket, object_key, data, PDF_MIME_TYPE)

    document = Document(
        id=document_id,
        original_filename=filename,
        mime_type=mime_type,
        file_size=len(data),
        page_count=page_count,
        minio_bucket=bucket,
        minio_object_key=object_key,
        status=DocumentStatus.UPLOADED,
    )
    db.add(document)
    try:
        await db.commit()
    except Exception:
        # Postgres failed after a successful MinIO upload: clean up the orphaned
        # object rather than silently losing track of it.
        await db.rollback()
        try:
            storage.delete(bucket, object_key)
        except Exception:
            logger.error(
                "orphaned_object_cleanup_failed",
                extra={"bucket": bucket, "key": object_key},
            )
        raise
    await db.refresh(document)
    return document


async def get_document(db: AsyncSession, document_id: uuid.UUID) -> Document:
    document = await db.get(Document, document_id)
    if document is None or document.status == DocumentStatus.DELETED:
        raise DocumentNotFoundError("Document not found.")
    return document


async def get_document_bytes(db: AsyncSession, storage: ObjectStorage, document_id: uuid.UUID) -> bytes:
    document = await get_document(db, document_id)
    return storage.download(document.minio_bucket, document.minio_object_key)


async def delete_document(db: AsyncSession, storage: ObjectStorage, document_id: uuid.UUID) -> None:
    document = await get_document(db, document_id)
    storage.delete(document.minio_bucket, document.minio_object_key)
    await db.delete(document)
    await db.commit()

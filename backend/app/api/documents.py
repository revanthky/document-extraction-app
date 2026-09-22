from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_config, get_storage
from app.config import AppConfig
from app.db.base import get_db
from app.pdf import service as pdf_service
from app.schemas.documents import DocumentResponse
from app.services import document_service
from app.storage.base import ObjectStorage

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
    storage: ObjectStorage = Depends(get_storage),
    config: AppConfig = Depends(get_config),
) -> DocumentResponse:
    data = await file.read()
    document = await document_service.upload_document(
        db,
        storage,
        config.minio_bucket_documents,
        filename=file.filename or "document.pdf",
        mime_type=file.content_type or "application/octet-stream",
        data=data,
        max_size_bytes=config.max_pdf_size_mb * 1024 * 1024,
    )
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> DocumentResponse:
    document = await document_service.get_document(db, document_id)
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}/pages/{page_num}")
async def get_document_page(
    document_id: uuid.UUID,
    page_num: int,
    db: AsyncSession = Depends(get_db),
    storage: ObjectStorage = Depends(get_storage),
    config: AppConfig = Depends(get_config),
) -> Response:
    pdf_bytes = await document_service.get_document_bytes(db, storage, document_id)
    page = pdf_service.render_page(pdf_bytes, page_num, dpi=config.pdf_render_dpi)
    return Response(content=page.png_bytes, media_type="image/png")


@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    storage: ObjectStorage = Depends(get_storage),
) -> Response:
    document = await document_service.get_document(db, document_id)
    pdf_bytes = storage.download(document.minio_bucket, document.minio_object_key)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{document.original_filename}"'},
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    storage: ObjectStorage = Depends(get_storage),
) -> dict:
    await document_service.delete_document(db, storage, document_id)
    return {"status": "deleted"}

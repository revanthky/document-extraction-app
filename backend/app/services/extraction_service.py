from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import ModelSettings
from app.core.exceptions import AppError, ExtractionNotFoundError
from app.core.logging import get_logger
from app.db.models import (
    Extraction,
    ExtractionField,
    ExtractionResult,
    ExtractionStatus,
    FieldResultStatus,
)
from app.pdf import service as pdf_service
from app.schemas.extractions import ExtractionFieldCreate
from app.services import document_service
from app.storage.base import ObjectStorage
from app.vision.base import VisionModelProvider
from app.vision.prompt import FieldSpec

logger = get_logger(__name__)

LOW_CONFIDENCE_THRESHOLD = 0.7


async def create_extraction(
    db: AsyncSession,
    storage: ObjectStorage,
    provider: VisionModelProvider,
    settings: ModelSettings,
    *,
    document_id: uuid.UUID,
    fields: list[ExtractionFieldCreate],
    instructions: str,
) -> Extraction:
    document = await document_service.get_document(db, document_id)

    extraction = Extraction(
        document_id=document.id,
        status=ExtractionStatus.PENDING,
        model_provider=settings.provider,
        model_name=settings.model_name,
        instructions=instructions,
        fields_requested=len(fields),
    )
    for order, field in enumerate(fields):
        extraction.fields.append(
            ExtractionField(
                name=field.name,
                display_name=field.resolved_display_name(),
                description=field.description,
                data_type=field.data_type,
                required=field.required,
                sort_order=order,
            )
        )
    db.add(extraction)
    await db.commit()
    await db.refresh(extraction, attribute_names=["fields"])

    extraction.status = ExtractionStatus.PROCESSING
    await db.commit()

    started = time.monotonic()
    try:
        pdf_bytes = storage.download(document.minio_bucket, document.minio_object_key)
        pages = pdf_service.render_all_pages(pdf_bytes, dpi=settings.pdf_render_dpi)

        field_specs = [
            FieldSpec(
                name=f.name, description=f.description or "", data_type=f.data_type, required=f.required
            )
            for f in extraction.fields
        ]

        call_result = await provider.extract(pages, field_specs, instructions)

        by_name = {f.name: f for f in call_result.response.fields}
        found = 0
        not_found = 0
        validation_failures = 0

        for extraction_field in extraction.fields:
            item = by_name.get(extraction_field.name)
            if item is None or item.value is None:
                not_found += 1
                db.add(
                    ExtractionResult(
                        extraction_id=extraction.id,
                        field_id=extraction_field.id,
                        value=None,
                        status=FieldResultStatus.NOT_FOUND,
                        page=item.page if item else None,
                        evidence=item.evidence if item else None,
                        confidence=item.confidence if item else None,
                        validation_status="NOT_FOUND",
                    )
                )
                continue

            found += 1
            validation_status = "OK"
            if item.confidence is not None and item.confidence < LOW_CONFIDENCE_THRESHOLD:
                validation_status = "LOW_CONFIDENCE"
                validation_failures += 1
            if extraction_field.required and item.value is None:
                validation_status = "MISSING_REQUIRED"
                validation_failures += 1

            db.add(
                ExtractionResult(
                    extraction_id=extraction.id,
                    field_id=extraction_field.id,
                    value=item.value,
                    confidence=item.confidence,
                    status=FieldResultStatus.FOUND,
                    page=item.page,
                    evidence=item.evidence,
                    validation_status=validation_status,
                )
            )

        extraction.status = ExtractionStatus.COMPLETED
        extraction.processing_time_ms = int((time.monotonic() - started) * 1000)
        extraction.fields_extracted = found
        extraction.fields_not_found = not_found
        extraction.validation_failures = validation_failures
        extraction.completed_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(
            "extraction_completed",
            extra={
                "extraction_id": str(extraction.id),
                "document_id": str(document.id),
                "fields_requested": len(fields),
                "fields_extracted": found,
                "processing_time_ms": extraction.processing_time_ms,
            },
        )
        return extraction

    except AppError as exc:
        extraction.status = ExtractionStatus.FAILED
        extraction.error_message = exc.message
        extraction.processing_time_ms = int((time.monotonic() - started) * 1000)
        await db.commit()
        logger.error(
            "extraction_failed",
            extra={"extraction_id": str(extraction.id), "error": exc.message},
        )
        raise


async def get_extraction(db: AsyncSession, extraction_id: uuid.UUID) -> Extraction:
    result = await db.execute(
        select(Extraction)
        .options(selectinload(Extraction.fields), selectinload(Extraction.results))
        .where(Extraction.id == extraction_id)
    )
    extraction = result.scalar_one_or_none()
    if extraction is None:
        raise ExtractionNotFoundError("Extraction not found.")
    return extraction

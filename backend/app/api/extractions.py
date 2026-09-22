from __future__ import annotations

import csv
import io
import json
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_model_settings, get_provider, get_storage
from app.config import ModelSettings
from app.db.base import get_db
from app.db.models import Extraction, ExtractionResult
from app.schemas.extractions import (
    CreateExtractionRequest,
    ExtractionResponse,
    ExtractionResultItem,
    ExtractionResultResponse,
)
from app.services import extraction_service
from app.storage.base import ObjectStorage
from app.vision.base import VisionModelProvider

router = APIRouter(prefix="/api/extractions", tags=["extractions"])


def _build_result_items(extraction: Extraction) -> list[ExtractionResultItem]:
    results_by_field: dict[uuid.UUID, ExtractionResult] = {
        r.field_id: r for r in extraction.results
    }
    items = []
    for field in extraction.fields:
        result = results_by_field.get(field.id)
        items.append(
            ExtractionResultItem(
                field_id=field.id,
                name=field.name,
                display_name=field.display_name,
                data_type=field.data_type,
                required=field.required,
                value=result.value if result else None,
                normalized_value=result.normalized_value if result else None,
                confidence=result.confidence if result else None,
                status=result.status if result else "NOT_FOUND",
                page=result.page if result else None,
                document_section=result.document_section if result else None,
                evidence=result.evidence if result else None,
                bounding_box=result.bounding_box if result else None,
                validation_status=result.validation_status if result else None,
                is_verified=result.is_verified if result else False,
                is_user_edited=result.is_user_edited if result else False,
            )
        )
    return items


@router.post("", response_model=ExtractionResponse)
async def create_extraction(
    payload: CreateExtractionRequest,
    db: AsyncSession = Depends(get_db),
    storage: ObjectStorage = Depends(get_storage),
    provider: VisionModelProvider = Depends(get_provider),
    settings: ModelSettings = Depends(get_current_model_settings),
) -> ExtractionResponse:
    extraction = await extraction_service.create_extraction(
        db,
        storage,
        provider,
        settings,
        document_id=payload.document_id,
        fields=payload.fields,
        instructions=payload.instructions,
    )
    return ExtractionResponse.model_validate(extraction)


@router.get("/{extraction_id}", response_model=ExtractionResponse)
async def get_extraction(extraction_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> ExtractionResponse:
    extraction = await extraction_service.get_extraction(db, extraction_id)
    return ExtractionResponse.model_validate(extraction)


@router.get("/{extraction_id}/result", response_model=ExtractionResultResponse)
async def get_extraction_result(
    extraction_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> ExtractionResultResponse:
    extraction = await extraction_service.get_extraction(db, extraction_id)
    return ExtractionResultResponse(
        extraction=ExtractionResponse.model_validate(extraction),
        results=_build_result_items(extraction),
    )


@router.get("/{extraction_id}/download/json")
async def download_json(extraction_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Response:
    extraction = await extraction_service.get_extraction(db, extraction_id)
    items = _build_result_items(extraction)
    payload = {
        "extraction_id": str(extraction.id),
        "document_id": str(extraction.document_id),
        "fields": [
            {
                "name": i.name,
                "display_name": i.display_name,
                "value": i.value,
                "confidence": float(i.confidence) if i.confidence is not None else None,
                "page": i.page,
                "evidence": i.evidence,
                "status": i.status,
            }
            for i in items
        ],
    }
    body = json.dumps(payload, indent=2, default=str)
    return Response(
        content=body,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="extraction_{extraction.id}.json"'},
    )


@router.get("/{extraction_id}/download/csv")
async def download_csv(extraction_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Response:
    extraction = await extraction_service.get_extraction(db, extraction_id)
    items = _build_result_items(extraction)

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Field", "Value", "Confidence", "Page", "Status", "Evidence"])
    for i in items:
        confidence_pct = f"{float(i.confidence) * 100:.0f}%" if i.confidence is not None else ""
        writer.writerow(
            [i.display_name, i.value if i.value is not None else "", confidence_pct, i.page or "", i.status, i.evidence or ""]
        )

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="extraction_{extraction.id}.csv"'},
    )

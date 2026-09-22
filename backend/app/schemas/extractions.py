from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.db.models import DataType


class ExtractionFieldCreate(BaseModel):
    name: str = Field(min_length=1)
    display_name: str | None = None
    description: str = ""
    data_type: str = DataType.STRING
    required: bool = False

    def resolved_display_name(self) -> str:
        return self.display_name or self.name


class CreateExtractionRequest(BaseModel):
    document_id: uuid.UUID
    fields: list[ExtractionFieldCreate] = Field(min_length=1)
    instructions: str = ""


class ExtractionResponse(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    status: str
    model_provider: str
    model_name: str
    instructions: str | None
    processing_time_ms: int | None
    fields_requested: int
    fields_extracted: int
    fields_not_found: int
    validation_failures: int
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class ExtractionResultItem(BaseModel):
    field_id: uuid.UUID
    name: str
    display_name: str
    data_type: str
    required: bool
    value: object | None
    normalized_value: object | None
    confidence: Decimal | None
    status: str
    page: int | None
    document_section: str | None
    evidence: str | None
    bounding_box: dict | None
    validation_status: str | None
    is_verified: bool
    is_user_edited: bool


class ExtractionResultResponse(BaseModel):
    extraction: ExtractionResponse
    results: list[ExtractionResultItem]

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DocumentStatus:
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DELETED = "DELETED"


class ExtractionStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FieldResultStatus:
    FOUND = "FOUND"
    NOT_FOUND = "NOT_FOUND"
    ERROR = "ERROR"


class DataType:
    STRING = "String"
    INTEGER = "Integer"
    DECIMAL = "Decimal"
    DATE = "Date"
    BOOLEAN = "Boolean"
    EMAIL = "Email"
    PHONE = "Phone"
    CURRENCY = "Currency"

    ALL = (STRING, INTEGER, DECIMAL, DATE, BOOLEAN, EMAIL, PHONE, CURRENCY)


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = _uuid_pk()
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[str] = mapped_column(String, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    minio_bucket: Mapped[str] = mapped_column(String, nullable=False)
    minio_object_key: Mapped[str] = mapped_column(String, nullable=False)
    document_type: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default=DocumentStatus.UPLOADING)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    extractions: Mapped[list[Extraction]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    sections: Mapped[list[DocumentSection]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Extraction(Base):
    __tablename__ = "extractions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False, default=ExtractionStatus.PENDING)
    model_provider: Mapped[str] = mapped_column(String, nullable=False)
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fields_requested: Mapped[int] = mapped_column(Integer, default=0)
    fields_extracted: Mapped[int] = mapped_column(Integer, default=0)
    fields_not_found: Mapped[int] = mapped_column(Integer, default=0)
    validation_failures: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped[Document] = relationship(back_populates="extractions")
    fields: Mapped[list[ExtractionField]] = relationship(
        back_populates="extraction", cascade="all, delete-orphan", order_by="ExtractionField.sort_order"
    )
    results: Mapped[list[ExtractionResult]] = relationship(
        back_populates="extraction", cascade="all, delete-orphan"
    )


class ExtractionField(Base):
    __tablename__ = "extraction_fields"

    id: Mapped[uuid.UUID] = _uuid_pk()
    extraction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extractions.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_type: Mapped[str] = mapped_column(String, nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    extraction: Mapped[Extraction] = relationship(back_populates="fields")
    result: Mapped[ExtractionResult | None] = relationship(
        back_populates="field", uselist=False, cascade="all, delete-orphan"
    )


class ExtractionResult(Base):
    __tablename__ = "extraction_results"

    id: Mapped[uuid.UUID] = _uuid_pk()
    extraction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extractions.id", ondelete="CASCADE"), nullable=False
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("extraction_fields.id", ondelete="CASCADE"), nullable=False
    )
    value: Mapped[dict | list | str | float | bool | None] = mapped_column(JSONB, nullable=True)
    normalized_value: Mapped[dict | list | str | float | bool | None] = mapped_column(
        JSONB, nullable=True
    )
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default=FieldResultStatus.NOT_FOUND)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    document_section: Mapped[str | None] = mapped_column(String, nullable=True)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    bounding_box: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    validation_status: Mapped[str | None] = mapped_column(String, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_user_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    original_value: Mapped[dict | list | str | float | bool | None] = mapped_column(
        JSONB, nullable=True
    )
    edited_value: Mapped[dict | list | str | float | bool | None] = mapped_column(
        JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    extraction: Mapped[Extraction] = relationship(back_populates="results")
    field: Mapped[ExtractionField] = relationship(back_populates="result")


class DocumentSection(Base):
    __tablename__ = "document_sections"

    id: Mapped[uuid.UUID] = _uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    section_type: Mapped[str] = mapped_column(String, nullable=False)
    start_page: Mapped[int] = mapped_column(Integer, nullable=False)
    end_page: Mapped[int] = mapped_column(Integer, nullable=False)
    section_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    document: Mapped[Document] = relationship(back_populates="sections")

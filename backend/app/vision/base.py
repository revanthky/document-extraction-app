from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.pdf.service import RenderedPage
from app.vision.prompt import ExtractionResponseSchema, FieldSpec


@dataclass
class ModelInfo:
    id: str


@dataclass
class ExtractionCallResult:
    response: ExtractionResponseSchema
    raw_text: str
    latency_ms: int


@dataclass
class ConnectionTestResult:
    success: bool
    message: str
    response_time_ms: int | None = None


class VisionModelProvider(ABC):
    """Abstraction over any vision-capable chat completion API.

    No PDF-specific or model-specific logic belongs here or in callers of
    this interface -- implementations only ever see rendered page images,
    field specs, and instructions.
    """

    @abstractmethod
    async def extract(
        self,
        pages: list[RenderedPage],
        fields: list[FieldSpec],
        instructions: str,
    ) -> ExtractionCallResult: ...

    @abstractmethod
    async def test_connection(self) -> ConnectionTestResult: ...

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]: ...

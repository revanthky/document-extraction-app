from __future__ import annotations

from app.core.exceptions import (
    ModelAuthError,
    ModelRateLimitError,
    ModelResponseError,
    ModelTimeoutError,
)
from app.pdf.service import RenderedPage
from app.vision.base import (
    ConnectionTestResult,
    ExtractionCallResult,
    ModelInfo,
    VisionModelProvider,
)
from app.vision.prompt import ExtractedFieldSchema, ExtractionResponseSchema, FieldSpec


class MockVisionModelProvider(VisionModelProvider):
    """Configurable stand-in for a real Vision Model, used across the test suite."""

    def __init__(
        self,
        mode: str = "success",
        field_values: dict[str, dict] | None = None,
        raw_text_override: str | None = None,
    ):
        self.mode = mode
        self.field_values = field_values or {}
        self.raw_text_override = raw_text_override
        self.calls: list[tuple[list[RenderedPage], list[FieldSpec], str]] = []

    async def extract(
        self, pages: list[RenderedPage], fields: list[FieldSpec], instructions: str
    ) -> ExtractionCallResult:
        self.calls.append((pages, fields, instructions))

        if self.mode == "auth_error":
            raise ModelAuthError("Vision Model authentication failed.")
        if self.mode == "rate_limit":
            raise ModelRateLimitError("Vision Model rate limit exceeded.")
        if self.mode == "timeout":
            raise ModelTimeoutError("The Vision Model request timed out.")
        if self.mode == "malformed":
            raise ModelResponseError("The Vision Model did not return valid structured data.")

        extracted = []
        for f in fields:
            defaults = {"value": f"mock-{f.name}", "confidence": 0.95, "page": 1, "evidence": f"mock evidence for {f.name}"}
            defaults.update(self.field_values.get(f.name, {}))
            extracted.append(ExtractedFieldSchema(name=f.name, **defaults))

        response = ExtractionResponseSchema(fields=extracted)
        return ExtractionCallResult(
            response=response,
            raw_text=self.raw_text_override or response.model_dump_json(),
            latency_ms=10,
        )

    async def test_connection(self) -> ConnectionTestResult:
        if self.mode == "auth_error":
            return ConnectionTestResult(success=False, message="Authentication failed.")
        return ConnectionTestResult(success=True, message="Connection successful", response_time_ms=5)

    async def list_models(self) -> list[ModelInfo]:
        return [ModelInfo(id="mock-model-a"), ModelInfo(id="mock-model-b")]

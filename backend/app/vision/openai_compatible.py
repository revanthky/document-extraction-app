from __future__ import annotations

import base64
import time

import httpx

from app.core.exceptions import (
    ModelAuthError,
    ModelRateLimitError,
    ModelResponseError,
    ModelTimeoutError,
)
from app.core.logging import get_logger
from app.pdf.service import RenderedPage
from app.vision.base import (
    ConnectionTestResult,
    ExtractionCallResult,
    ModelInfo,
    VisionModelProvider,
)
from app.vision.prompt import (
    ExtractionResponseSchema,
    FieldSpec,
    build_prompt,
    parse_and_validate_response,
)

logger = get_logger(__name__)


class OpenAICompatibleProvider(VisionModelProvider):
    """Works against any OpenAI-compatible vision chat completion API.

    This includes vLLM, OpenAI itself, and DKubeX SecureLLM (which is just an
    OpenAI-compatible endpoint at `https://<host>/securellm/v1`). No
    provider-specific branching lives here or anywhere upstream of it.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model_name: str,
        temperature: float = 0,
        max_tokens: int = 4096,
        timeout: int = 120,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model_name = model_name
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _image_content_blocks(self, pages: list[RenderedPage]) -> list[dict]:
        blocks = []
        for page in pages:
            b64 = base64.b64encode(page.png_bytes).decode("ascii")
            blocks.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                }
            )
        return blocks

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code == 401:
            raise ModelAuthError(
                "Vision Model authentication failed. Check the configured API key.",
                detail=response.text[:500],
            )
        if response.status_code == 429:
            raise ModelRateLimitError(
                "Vision Model rate limit exceeded. Try again shortly.",
                detail=response.text[:500],
            )
        if response.status_code >= 400:
            raise ModelResponseError(
                f"Vision Model request failed with status {response.status_code}.",
                detail=response.text[:500],
            )

    async def extract(
        self,
        pages: list[RenderedPage],
        fields: list[FieldSpec],
        instructions: str,
    ) -> ExtractionCallResult:
        prompt = build_prompt(fields, instructions)
        content = [{"type": "text", "text": prompt}, *self._image_content_blocks(pages)]

        payload = {
            "model": self._model_name,
            "messages": [{"role": "user", "content": content}],
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }

        started = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers=self._headers(),
                    json=payload,
                )
        except httpx.TimeoutException as exc:
            raise ModelTimeoutError("The Vision Model request timed out.") from exc
        except httpx.RequestError as exc:
            raise ModelResponseError(f"Failed to reach the Vision Model endpoint: {exc}") from exc

        latency_ms = int((time.monotonic() - started) * 1000)
        self._raise_for_status(response)

        try:
            body = response.json()
            raw_text = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as exc:
            raise ModelResponseError(
                "Vision Model response did not match the expected chat completion shape.",
                detail=response.text[:500],
            ) from exc

        parsed = self._validate_against_requested_fields(
            parse_and_validate_response(raw_text), fields
        )
        return ExtractionCallResult(response=parsed, raw_text=raw_text, latency_ms=latency_ms)

    def _validate_against_requested_fields(
        self, response: ExtractionResponseSchema, fields: list[FieldSpec]
    ) -> ExtractionResponseSchema:
        returned = {f.name for f in response.fields}
        requested = {f.name for f in fields}
        missing = requested - returned
        if missing:
            logger.warning("extraction_missing_fields", extra={"missing_fields": sorted(missing)})
        return response

    async def test_connection(self) -> ConnectionTestResult:
        started = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{self._base_url}/models", headers=self._headers())
        except httpx.TimeoutException:
            return ConnectionTestResult(success=False, message="Connection timed out.")
        except httpx.RequestError as exc:
            return ConnectionTestResult(success=False, message=f"Could not reach endpoint: {exc}")

        elapsed_ms = int((time.monotonic() - started) * 1000)

        if response.status_code == 401:
            return ConnectionTestResult(success=False, message="Authentication failed.", response_time_ms=elapsed_ms)
        if response.status_code >= 400:
            return ConnectionTestResult(
                success=False,
                message=f"Endpoint returned status {response.status_code}.",
                response_time_ms=elapsed_ms,
            )

        try:
            model_ids = [m["id"] for m in response.json().get("data", [])]
        except (ValueError, TypeError):
            model_ids = []

        if self._model_name and model_ids and self._model_name not in model_ids:
            return ConnectionTestResult(
                success=False,
                message=f"Model '{self._model_name}' was not found at this endpoint.",
                response_time_ms=elapsed_ms,
            )

        return ConnectionTestResult(
            success=True, message="Connection successful", response_time_ms=elapsed_ms
        )

    async def list_models(self) -> list[ModelInfo]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(f"{self._base_url}/models", headers=self._headers())
        except httpx.TimeoutException as exc:
            raise ModelTimeoutError("Timed out while fetching available models.") from exc
        except httpx.RequestError as exc:
            raise ModelResponseError(f"Failed to reach the Vision Model endpoint: {exc}") from exc
        self._raise_for_status(response)
        try:
            data = response.json().get("data", [])
        except ValueError as exc:
            raise ModelResponseError("Vision Model /models response was not valid JSON.") from exc
        models = sorted({m["id"] for m in data if "id" in m})
        return [ModelInfo(id=m) for m in models]

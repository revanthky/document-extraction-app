from __future__ import annotations

from app.config import ModelSettings
from app.core.exceptions import ModelNotConfiguredError
from app.vision.base import VisionModelProvider
from app.vision.openai_compatible import OpenAICompatibleProvider


def build_provider(settings: ModelSettings) -> VisionModelProvider:
    if not settings.api_base_url or not settings.model_name:
        raise ModelNotConfiguredError(
            "Vision Model is not configured. Set an API base URL and model name in Settings."
        )
    return OpenAICompatibleProvider(
        base_url=settings.api_base_url,
        api_key=settings.api_key,
        model_name=settings.model_name,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        timeout=settings.timeout,
    )

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_provider, get_store
from app.config import ModelSettings, SettingsStore
from app.schemas.settings import (
    FetchModelsRequest,
    FetchModelsResponse,
    ModelSettingsResponse,
    ModelSettingsUpdateRequest,
    TestConnectionResponse,
)
from app.vision.base import VisionModelProvider
from app.vision.openai_compatible import OpenAICompatibleProvider

router = APIRouter(prefix="/api/settings/model", tags=["settings"])


def _to_response(settings: ModelSettings) -> ModelSettingsResponse:
    masked = settings.masked()
    return ModelSettingsResponse(
        provider=settings.provider,
        api_base_url=settings.api_base_url,
        api_key_masked=masked.api_key,
        api_key_configured=bool(settings.api_key),
        model_name=settings.model_name,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        timeout=settings.timeout,
        pdf_render_dpi=settings.pdf_render_dpi,
    )


@router.get("", response_model=ModelSettingsResponse)
async def get_model_settings(store: SettingsStore = Depends(get_store)) -> ModelSettingsResponse:
    return _to_response(store.load())


@router.put("", response_model=ModelSettingsResponse)
async def update_model_settings(
    payload: ModelSettingsUpdateRequest, store: SettingsStore = Depends(get_store)
) -> ModelSettingsResponse:
    current = store.load()
    new_settings = ModelSettings(
        provider=payload.provider,
        api_base_url=payload.api_base_url,
        api_key=payload.api_key if payload.api_key is not None else current.api_key,
        model_name=payload.model_name,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        timeout=payload.timeout,
        pdf_render_dpi=payload.pdf_render_dpi,
    )
    store.save(new_settings)
    return _to_response(new_settings)


@router.post("/test", response_model=TestConnectionResponse)
async def test_connection(
    store: SettingsStore = Depends(get_store), provider: VisionModelProvider = Depends(get_provider)
) -> TestConnectionResponse:
    settings = store.load()
    result = await provider.test_connection()
    return TestConnectionResponse(
        success=result.success,
        message=result.message,
        model=settings.model_name if result.success else None,
        response_time_ms=result.response_time_ms,
    )


@router.post("/models", response_model=FetchModelsResponse)
async def fetch_models(payload: FetchModelsRequest) -> FetchModelsResponse:
    provider = OpenAICompatibleProvider(
        base_url=payload.api_base_url, api_key=payload.api_key or "", model_name=""
    )
    models = await provider.list_models()
    return FetchModelsResponse(models=sorted(m.id for m in models))

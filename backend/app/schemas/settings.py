from __future__ import annotations

from pydantic import BaseModel, Field


class ModelSettingsResponse(BaseModel):
    provider: str
    api_base_url: str
    api_key_masked: str
    api_key_configured: bool
    model_name: str
    temperature: float
    max_tokens: int
    timeout: int
    pdf_render_dpi: int


class ModelSettingsUpdateRequest(BaseModel):
    provider: str = "openai_compatible"
    api_base_url: str
    api_key: str | None = None
    model_name: str
    temperature: float = Field(default=0, ge=0, le=2)
    max_tokens: int = Field(default=4096, gt=0)
    timeout: int = Field(default=120, gt=0)
    pdf_render_dpi: int = Field(default=150, ge=72, le=600)


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    model: str | None = None
    response_time_ms: int | None = None


class FetchModelsRequest(BaseModel):
    api_base_url: str
    api_key: str | None = None


class FetchModelsResponse(BaseModel):
    models: list[str]

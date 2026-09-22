from __future__ import annotations

import json
import os
import stat
import threading
from pathlib import Path

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_async_database_url(raw: str) -> str:
    """Ensure a Postgres URL names the asyncpg driver SQLAlchemy's async engine needs.

    DKubeX's auto-provisioned `postgres` dependency injects a bare `postgresql://` URL
    (see package-app skill, references/dependencies.md); local dev already writes
    `postgresql+asyncpg://`. Accept either.
    """
    if raw.startswith("postgresql://"):
        return "postgresql+asyncpg://" + raw[len("postgresql://") :]
    return raw


class AppConfig(BaseSettings):
    """Environment-driven application configuration."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"
    max_pdf_size_mb: int = 25
    cors_origins: str = "http://localhost:5173"

    model_provider: str = "openai_compatible"
    model_base_url: str = "http://localhost:8000/v1"
    model_name: str = "vision-model"
    model_api_key: str = ""
    model_timeout: int = 120
    model_temperature: float = 0
    model_max_tokens: int = 4096
    pdf_render_dpi: int = 150
    settings_file: str = "./.data/model_settings.json"

    database_url: str = (
        "postgresql+asyncpg://document_extractor:document_extractor@localhost:5432/document_extractor"
    )

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_documents: str = "documents"

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        return normalize_async_database_url(value)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


class ModelSettings(BaseModel):
    """User-configurable Vision Model settings, persisted to a JSON file."""

    provider: str = "openai_compatible"
    api_base_url: str = ""
    api_key: str = ""
    model_name: str = ""
    temperature: float = 0
    max_tokens: int = 4096
    timeout: int = 120
    pdf_render_dpi: int = 150

    def masked(self) -> ModelSettings:
        masked = self.model_copy()
        if masked.api_key:
            masked.api_key = "*" * min(len(masked.api_key), 16)
        return masked


class SettingsStore:
    """Loads/persists ModelSettings to a JSON file with 0600 permissions.

    Falls back to .env-derived defaults when no settings file exists yet, so a
    freshly-deployed instance is still usable without manual configuration.
    """

    def __init__(self, app_config: AppConfig):
        self._app_config = app_config
        self._path = Path(app_config.settings_file)
        self._lock = threading.Lock()
        self._cached: ModelSettings | None = None

    def _defaults(self) -> ModelSettings:
        return ModelSettings(
            provider=self._app_config.model_provider,
            api_base_url=self._app_config.model_base_url,
            api_key=self._app_config.model_api_key,
            model_name=self._app_config.model_name,
            temperature=self._app_config.model_temperature,
            max_tokens=self._app_config.model_max_tokens,
            timeout=self._app_config.model_timeout,
            pdf_render_dpi=self._app_config.pdf_render_dpi,
        )

    def load(self) -> ModelSettings:
        with self._lock:
            if self._cached is not None:
                return self._cached
            if self._path.exists():
                data = json.loads(self._path.read_text())
                self._cached = ModelSettings.model_validate(data)
            else:
                self._cached = self._defaults()
            return self._cached

    def save(self, settings: ModelSettings) -> ModelSettings:
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self._path.with_suffix(".tmp")
            tmp_path.write_text(settings.model_dump_json(indent=2))
            os.chmod(tmp_path, stat.S_IRUSR | stat.S_IWUSR)
            tmp_path.replace(self._path)
            os.chmod(self._path, stat.S_IRUSR | stat.S_IWUSR)
            self._cached = settings
            return settings


_app_config: AppConfig | None = None
_settings_store: SettingsStore | None = None


def get_app_config() -> AppConfig:
    global _app_config
    if _app_config is None:
        _app_config = AppConfig()
    return _app_config


def get_settings_store() -> SettingsStore:
    global _settings_store
    if _settings_store is None:
        _settings_store = SettingsStore(get_app_config())
    return _settings_store

from __future__ import annotations

from app.config import (
    AppConfig,
    ModelSettings,
    SettingsStore,
    get_app_config,
    get_settings_store,
)
from app.storage.base import ObjectStorage
from app.storage.minio_storage import get_object_storage
from app.vision.base import VisionModelProvider
from app.vision.factory import build_provider


def get_config() -> AppConfig:
    return get_app_config()


def get_store() -> SettingsStore:
    return get_settings_store()


def get_storage() -> ObjectStorage:
    return get_object_storage()


def get_current_model_settings() -> ModelSettings:
    return get_settings_store().load()


def get_provider() -> VisionModelProvider:
    return build_provider(get_current_model_settings())

from __future__ import annotations

import io
import os

import pytest
from httpx import ASGITransport, AsyncClient
from reportlab.pdfgen import canvas
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

os.environ.setdefault("SETTINGS_FILE", "/tmp/document_extraction_test_settings.json")

from app.api import deps
from app.db.base import Base
from app.storage.minio_storage import MinIOObjectStorage
from tests.mock_provider import MockVisionModelProvider

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://document_extractor:document_extractor@localhost:5432/document_extractor_test",
)
TEST_MINIO_BUCKET = "documents-test"


def make_pdf_bytes(num_pages: int = 1, texts: list[str] | None = None) -> bytes:
    """Generate a small, real, synthetic PDF for tests -- no fixture binaries checked in."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    for i in range(num_pages):
        text = texts[i] if texts and i < len(texts) else f"Synthetic page {i + 1}"
        c.drawString(72, 720, text)
        c.showPage()
    c.save()
    return buffer.getvalue()


@pytest.fixture
async def db_engine():
    # Function-scoped (not session-scoped): asyncpg connections are bound to the
    # event loop they were created on, and pytest-asyncio gives each test its own
    # loop, so a shared engine/pool across tests causes cross-loop errors.
    engine = create_async_engine(TEST_DATABASE_URL)
    yield engine
    await engine.dispose()


@pytest.fixture(autouse=True)
async def _reset_schema(db_engine):
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
def session_factory(db_engine):
    return async_sessionmaker(bind=db_engine, expire_on_commit=False)


@pytest.fixture
async def db_session(session_factory):
    async with session_factory() as session:
        yield session


@pytest.fixture(scope="session")
def storage():
    store = MinIOObjectStorage(
        endpoint="localhost:9000", access_key="minioadmin", secret_key="minioadmin", secure=False
    )
    store.ensure_bucket(TEST_MINIO_BUCKET)
    return store


@pytest.fixture
def mock_provider():
    return MockVisionModelProvider(mode="success")


@pytest.fixture
def app_client(session_factory, storage, mock_provider):
    """A FastAPI TestClient-equivalent (async) with all external deps overridden."""
    from app.config import ModelSettings
    from app.main import app

    async def override_get_db():
        async with session_factory() as session:
            yield session

    def override_get_storage():
        return storage

    def override_get_config():
        cfg = deps.get_app_config()
        cfg.minio_bucket_documents = TEST_MINIO_BUCKET
        return cfg

    def override_get_current_model_settings():
        return ModelSettings(
            provider="openai_compatible",
            api_base_url="http://mock/v1",
            api_key="test-key",
            model_name="mock-model",
        )

    def override_get_provider():
        return mock_provider

    from app.db.base import get_db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[deps.get_storage] = override_get_storage
    app.dependency_overrides[deps.get_config] = override_get_config
    app.dependency_overrides[deps.get_current_model_settings] = override_get_current_model_settings
    app.dependency_overrides[deps.get_provider] = override_get_provider

    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://testserver")
    try:
        yield client
    finally:
        app.dependency_overrides.clear()

from __future__ import annotations

from app.config import normalize_async_database_url
from app.storage.minio_storage import split_endpoint


def test_bare_postgres_url_gets_asyncpg_driver():
    raw = "postgresql://app_doc:secret@postgres.dkubex.svc:5432/app_doc"
    assert normalize_async_database_url(raw) == (
        "postgresql+asyncpg://app_doc:secret@postgres.dkubex.svc:5432/app_doc"
    )


def test_already_qualified_postgres_url_is_left_alone():
    raw = "postgresql+asyncpg://document_extractor:document_extractor@localhost:5432/document_extractor"
    assert normalize_async_database_url(raw) == raw


def test_minio_endpoint_with_http_scheme_is_split():
    endpoint, secure = split_endpoint("http://minio.dkubex.svc:9000", default_secure=True)
    assert endpoint == "minio.dkubex.svc:9000"
    assert secure is False


def test_minio_endpoint_with_https_scheme_is_split():
    endpoint, secure = split_endpoint("https://minio.dkubex.svc:9000", default_secure=False)
    assert endpoint == "minio.dkubex.svc:9000"
    assert secure is True


def test_minio_endpoint_without_scheme_keeps_default_secure():
    endpoint, secure = split_endpoint("localhost:9000", default_secure=False)
    assert endpoint == "localhost:9000"
    assert secure is False

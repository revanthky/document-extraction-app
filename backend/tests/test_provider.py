from __future__ import annotations

import httpx
import pytest

from app.core.exceptions import (
    ModelAuthError,
    ModelRateLimitError,
    ModelResponseError,
    ModelTimeoutError,
)
from app.vision.openai_compatible import OpenAICompatibleProvider
from app.vision.prompt import FieldSpec
from tests.conftest import make_pdf_bytes
from tests.fake_httpx import FakeAsyncClient, make_response


def _provider() -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        base_url="http://mock/v1", api_key="secret", model_name="mock-model", timeout=5
    )


def _pages():
    from app.pdf.service import render_all_pages

    return render_all_pages(make_pdf_bytes(num_pages=1))


def _fields():
    return [FieldSpec(name="policy_number", description="", data_type="String", required=True)]


async def test_extract_success(monkeypatch):
    body = {
        "choices": [
            {
                "message": {
                    "content": (
                        '{"fields": [{"name": "policy_number", "value": "POL-1", '
                        '"confidence": 0.9, "page": 1, "evidence": "POL-1"}]}'
                    )
                }
            }
        ]
    }
    monkeypatch.setattr(
        "app.vision.openai_compatible.httpx.AsyncClient",
        lambda **kw: FakeAsyncClient(post_response=make_response(200, json_body=body)),
    )
    result = await _provider().extract(_pages(), _fields(), "")
    assert result.response.fields[0].value == "POL-1"
    assert result.latency_ms >= 0


async def test_extract_auth_error(monkeypatch):
    monkeypatch.setattr(
        "app.vision.openai_compatible.httpx.AsyncClient",
        lambda **kw: FakeAsyncClient(post_response=make_response(401, text="unauthorized")),
    )
    with pytest.raises(ModelAuthError):
        await _provider().extract(_pages(), _fields(), "")


async def test_extract_rate_limit(monkeypatch):
    monkeypatch.setattr(
        "app.vision.openai_compatible.httpx.AsyncClient",
        lambda **kw: FakeAsyncClient(post_response=make_response(429, text="slow down")),
    )
    with pytest.raises(ModelRateLimitError):
        await _provider().extract(_pages(), _fields(), "")


async def test_extract_timeout(monkeypatch):
    monkeypatch.setattr(
        "app.vision.openai_compatible.httpx.AsyncClient",
        lambda **kw: FakeAsyncClient(raise_on_post=httpx.TimeoutException("timed out")),
    )
    with pytest.raises(ModelTimeoutError):
        await _provider().extract(_pages(), _fields(), "")


async def test_extract_malformed_model_output_raises_model_response_error(monkeypatch):
    body = {"choices": [{"message": {"content": "not json"}}]}
    monkeypatch.setattr(
        "app.vision.openai_compatible.httpx.AsyncClient",
        lambda **kw: FakeAsyncClient(post_response=make_response(200, json_body=body)),
    )
    with pytest.raises(ModelResponseError):
        await _provider().extract(_pages(), _fields(), "")


async def test_extract_unexpected_response_shape_raises(monkeypatch):
    monkeypatch.setattr(
        "app.vision.openai_compatible.httpx.AsyncClient",
        lambda **kw: FakeAsyncClient(post_response=make_response(200, json_body={"unexpected": True})),
    )
    with pytest.raises(ModelResponseError):
        await _provider().extract(_pages(), _fields(), "")


async def test_test_connection_success(monkeypatch):
    monkeypatch.setattr(
        "app.vision.openai_compatible.httpx.AsyncClient",
        lambda **kw: FakeAsyncClient(
            get_response=make_response(200, json_body={"data": [{"id": "mock-model"}]})
        ),
    )
    result = await _provider().test_connection()
    assert result.success is True


async def test_test_connection_auth_failure(monkeypatch):
    monkeypatch.setattr(
        "app.vision.openai_compatible.httpx.AsyncClient",
        lambda **kw: FakeAsyncClient(get_response=make_response(401, text="nope")),
    )
    result = await _provider().test_connection()
    assert result.success is False


async def test_list_models_returns_sorted_ids(monkeypatch):
    monkeypatch.setattr(
        "app.vision.openai_compatible.httpx.AsyncClient",
        lambda **kw: FakeAsyncClient(
            get_response=make_response(
                200, json_body={"data": [{"id": "zeta"}, {"id": "alpha"}]}
            )
        ),
    )
    models = await _provider().list_models()
    assert [m.id for m in models] == ["alpha", "zeta"]

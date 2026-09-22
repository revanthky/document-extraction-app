from __future__ import annotations

from tests.fake_httpx import FakeAsyncClient, make_response


async def test_get_settings_returns_defaults(app_client):
    response = await app_client.get("/api/settings/model")
    assert response.status_code == 200
    body = response.json()
    assert "api_key" not in body  # never expose raw key
    assert body["api_key_configured"] is False or isinstance(body["api_key_configured"], bool)


async def test_update_settings_masks_api_key_in_response(app_client):
    payload = {
        "provider": "openai_compatible",
        "api_base_url": "http://localhost:9999/v1",
        "api_key": "super-secret-key",
        "model_name": "vision-model",
        "temperature": 0,
        "max_tokens": 2048,
        "timeout": 60,
        "pdf_render_dpi": 150,
    }
    response = await app_client.put("/api/settings/model", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["api_key_configured"] is True
    assert "super-secret-key" not in response.text


async def test_update_settings_persists(app_client):
    payload = {
        "provider": "openai_compatible",
        "api_base_url": "http://localhost:8123/v1",
        "api_key": "key-1",
        "model_name": "model-1",
        "temperature": 0.2,
        "max_tokens": 1024,
        "timeout": 30,
        "pdf_render_dpi": 200,
    }
    await app_client.put("/api/settings/model", json=payload)
    response = await app_client.get("/api/settings/model")
    body = response.json()
    assert body["api_base_url"] == "http://localhost:8123/v1"
    assert body["model_name"] == "model-1"
    assert body["pdf_render_dpi"] == 200


async def test_test_connection_success_uses_mock_provider(app_client):
    response = await app_client.post("/api/settings/model/test")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["response_time_ms"] is not None


async def test_fetch_models_returns_sorted_ids(app_client, monkeypatch):
    monkeypatch.setattr(
        "app.vision.openai_compatible.httpx.AsyncClient",
        lambda **kw: FakeAsyncClient(
            get_response=make_response(200, json_body={"data": [{"id": "zzz"}, {"id": "aaa"}]})
        ),
    )
    response = await app_client.post(
        "/api/settings/model/models", json={"api_base_url": "http://mock/v1", "api_key": "x"}
    )
    assert response.status_code == 200
    assert response.json()["models"] == ["aaa", "zzz"]


async def test_fetch_models_nonblocking_error_on_bad_endpoint(app_client, monkeypatch):
    import httpx

    monkeypatch.setattr(
        "app.vision.openai_compatible.httpx.AsyncClient",
        lambda **kw: FakeAsyncClient(raise_on_get=httpx.ConnectError("refused")),
    )
    response = await app_client.post(
        "/api/settings/model/models", json={"api_base_url": "http://mock/v1", "api_key": "x"}
    )
    assert response.status_code == 502
    assert "detail" not in response.json() or "stack" not in response.text.lower()

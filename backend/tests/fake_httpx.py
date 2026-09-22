from __future__ import annotations

import httpx


class FakeAsyncClient:
    """Minimal stand-in for httpx.AsyncClient used to unit-test the provider
    without making real network calls."""

    def __init__(self, *, get_response=None, post_response=None, raise_on_post=None, raise_on_get=None, **kwargs):
        self._get_response = get_response
        self._post_response = post_response
        self._raise_on_post = raise_on_post
        self._raise_on_get = raise_on_get

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, headers=None, json=None):
        if self._raise_on_post:
            raise self._raise_on_post
        return self._post_response

    async def get(self, url, headers=None):
        if self._raise_on_get:
            raise self._raise_on_get
        return self._get_response


def make_response(status_code: int, json_body: dict | None = None, text: str = "") -> httpx.Response:
    request = httpx.Request("POST", "http://mock/v1/chat/completions")
    if json_body is not None:
        return httpx.Response(status_code, json=json_body, request=request)
    return httpx.Response(status_code, text=text, request=request)

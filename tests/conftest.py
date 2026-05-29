"""Shared test helpers. All tests run against an in-memory httpx MockTransport."""

from __future__ import annotations

import json
from typing import Any, Callable, List, Optional

import httpx
import pytest

from anypost import Anypost, AsyncAnypost

BASE_URL = "https://api.anypost.test/v1"

Handler = Callable[[httpx.Request], httpx.Response]


class Recorder:
    """Records every request the client makes and serves canned responses."""

    def __init__(self, handler: Handler) -> None:
        self._handler = handler
        self.requests: List[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._handler(request)

    @property
    def last(self) -> httpx.Request:
        return self.requests[-1]

    def body(self, index: int = -1) -> Any:
        return json.loads(self.requests[index].content)


def json_response(
    status: int, payload: Any = None, headers: Optional[dict] = None
) -> httpx.Response:
    return httpx.Response(status, json=payload, headers=headers or {})


def make_client(handler: Handler, **kwargs: Any) -> tuple[Anypost, Recorder]:
    recorder = Recorder(handler)
    transport = httpx.MockTransport(recorder)
    http_client = httpx.Client(base_url=BASE_URL, transport=transport)
    client = Anypost(
        kwargs.pop("api_key", "ap_test"),
        http_client=http_client,
        **kwargs,
    )
    return client, recorder


def make_async_client(handler: Handler, **kwargs: Any) -> tuple[AsyncAnypost, Recorder]:
    recorder = Recorder(handler)
    transport = httpx.MockTransport(recorder)
    http_client = httpx.AsyncClient(base_url=BASE_URL, transport=transport)
    client = AsyncAnypost(
        kwargs.pop("api_key", "ap_test"),
        http_client=http_client,
        **kwargs,
    )
    return client, recorder


@pytest.fixture
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> List[float]:
    """Patch out the retry sleep, recording the durations it was asked for."""
    slept: List[float] = []

    def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    async def fake_async_sleep(seconds: float) -> None:
        slept.append(seconds)

    monkeypatch.setattr("anypost._http.time.sleep", fake_sleep)
    monkeypatch.setattr("anypost._async_http.asyncio.sleep", fake_async_sleep)
    # Deterministic full-jitter: random() -> 1.0 so backoff == ceiling.
    monkeypatch.setattr("anypost._http.random.random", lambda: 1.0)
    return slept

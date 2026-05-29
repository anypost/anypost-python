"""Async client: parity with the sync surface over httpx.AsyncClient."""

from __future__ import annotations

from typing import List

import httpx
import pytest
from conftest import json_response, make_async_client

from anypost import APIError, ValidationError

SENT = {"id": "email_async", "created_at": "t"}


def send_ok(_: httpx.Request) -> httpx.Response:
    return json_response(202, SENT)


def sequence(*responses):
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        i = min(calls["n"], len(responses) - 1)
        calls["n"] += 1
        result = responses[i]
        if isinstance(result, Exception):
            raise result
        return result

    return handler


async def test_send_and_headers() -> None:
    client, rec = make_async_client(send_ok)
    result = await client.email.send(
        {"from": "a@x.com", "to": ["b@y.com"], "text": "hi"}
    )
    assert result == SENT
    assert rec.last.headers["authorization"] == "Bearer ap_test"
    assert len(rec.last.headers["idempotency-key"]) == 36
    await client.aclose()


async def test_context_manager_and_whoami() -> None:
    body = {"team": None, "api_key": {"id": "k", "permissions": "send_only"}}
    async with make_async_client(lambda r: json_response(200, body))[0] as client:
        me = await client.whoami()
    assert me["api_key"]["permissions"] == "send_only"


async def test_async_pagination_iterates() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("after") is None:
            return json_response(
                200,
                {"data": [{"id": "d1"}], "has_more": True, "next_cursor": "c2"},
            )
        return json_response(
            200, {"data": [{"id": "d2"}], "has_more": False, "next_cursor": None}
        )

    client, _ = make_async_client(handler)
    ids = [d["id"] async for d in await client.domains.list()]
    assert ids == ["d1", "d2"]
    await client.aclose()


async def test_async_error_mapping() -> None:
    client, _ = make_async_client(
        lambda r: json_response(400, {"error": {"type": "validation_error"}}),
        max_retries=0,
    )
    with pytest.raises(ValidationError):
        await client.email.send({"from": "a@x.com", "to": ["b@y.com"], "text": "t"})
    await client.aclose()


async def test_async_retries_then_succeeds(no_sleep: List[float]) -> None:
    client, rec = make_async_client(
        sequence(json_response(503, {}), json_response(202, SENT))
    )
    result = await client.email.send({"from": "a@x.com", "to": ["b@y.com"], "text": "t"})
    assert result == SENT
    assert len(rec.requests) == 2
    assert no_sleep == [0.5]
    await client.aclose()


async def test_async_retries_reuse_idempotency_key(no_sleep: List[float]) -> None:
    client, rec = make_async_client(
        sequence(json_response(503, {}), json_response(202, SENT))
    )
    await client.email.send({"from": "a@x.com", "to": ["b@y.com"], "text": "t"})
    keys = {r.headers["idempotency-key"] for r in rec.requests}
    assert len(keys) == 1


async def test_async_exhausts_retries(no_sleep: List[float]) -> None:
    client, rec = make_async_client(sequence(json_response(503, {})), max_retries=1)
    with pytest.raises(APIError):
        await client.email.send({"from": "a@x.com", "to": ["b@y.com"], "text": "t"})
    assert len(rec.requests) == 2
    await client.aclose()

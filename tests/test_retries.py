"""Retry policy: which statuses retry, backoff, Retry-After, idempotency reuse."""

from __future__ import annotations

from typing import List

import httpx
import pytest
from conftest import json_response, make_client

from anypost import APIConnectionError, APIError, ValidationError

SENT = {"id": "email_1", "created_at": "t"}


def _send(client):
    return client.email.send({"from": "a@x.com", "to": ["b@y.com"], "text": "t"})


def sequence(*responses):
    """A handler that returns each response in turn, repeating the last."""
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        i = min(calls["n"], len(responses) - 1)
        calls["n"] += 1
        result = responses[i]
        if isinstance(result, Exception):
            raise result
        return result

    return handler


def test_retries_503_then_succeeds(no_sleep: List[float]) -> None:
    client, rec = make_client(
        sequence(json_response(503, {}), json_response(202, SENT))
    )
    assert _send(client) == SENT
    assert len(rec.requests) == 2
    assert len(no_sleep) == 1


def test_full_jitter_backoff_doubles(no_sleep: List[float]) -> None:
    client, _ = make_client(
        sequence(json_response(503, {}), json_response(502, {}), json_response(202, SENT))
    )
    _send(client)
    # random()==1.0, so backoff == ceiling: 0.5 * 2**attempt.
    assert no_sleep == [0.5, 1.0]


def test_retry_after_header_honored(no_sleep: List[float]) -> None:
    client, _ = make_client(
        sequence(
            json_response(429, {}, headers={"Retry-After": "2"}),
            json_response(202, SENT),
        )
    )
    _send(client)
    assert no_sleep == [2.0]


def test_exhausts_retries_then_raises(no_sleep: List[float]) -> None:
    client, rec = make_client(sequence(json_response(503, {})), max_retries=2)
    with pytest.raises(APIError):
        _send(client)
    assert len(rec.requests) == 3  # initial + 2 retries


def test_no_retry_on_4xx(no_sleep: List[float]) -> None:
    client, rec = make_client(
        sequence(json_response(400, {"error": {"type": "validation_error"}})),
        max_retries=2,
    )
    with pytest.raises(ValidationError):
        _send(client)
    assert len(rec.requests) == 1


def test_auto_idempotency_key_reused_across_retries(no_sleep: List[float]) -> None:
    client, rec = make_client(
        sequence(json_response(503, {}), json_response(503, {}), json_response(202, SENT))
    )
    _send(client)
    keys = {r.headers["idempotency-key"] for r in rec.requests}
    assert len(rec.requests) == 3
    assert len(keys) == 1  # one key, reused — a retried send cannot double-send


def test_network_error_retries_then_connection_error(no_sleep: List[float]) -> None:
    err = httpx.ConnectError("connection refused")
    client, rec = make_client(sequence(err), max_retries=1)
    with pytest.raises(APIConnectionError):
        _send(client)
    assert len(rec.requests) == 2  # initial + 1 retry


def test_network_error_recovers(no_sleep: List[float]) -> None:
    client, rec = make_client(
        sequence(httpx.ConnectError("boom"), json_response(202, SENT))
    )
    assert _send(client) == SENT
    assert len(rec.requests) == 2

"""Construction, env fallback, and header assembly."""

from __future__ import annotations

import platform

import httpx
import pytest
from conftest import json_response, make_client

from anypost import Anypost, __version__


def ok(_: httpx.Request) -> httpx.Response:
    return json_response(200, {"ok": True})


def test_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANYPOST_API_KEY", raising=False)
    with pytest.raises(ValueError, match="API key is required"):
        Anypost()


def test_reads_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANYPOST_API_KEY", "ap_from_env")
    client = Anypost()
    assert client is not None


def test_explicit_key_beats_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANYPOST_API_KEY", "ap_from_env")
    client, rec = make_client(ok, api_key="ap_explicit")
    client.whoami()
    assert rec.last.headers["authorization"] == "Bearer ap_explicit"


def test_default_headers_on_every_request() -> None:
    client, rec = make_client(ok)
    client.whoami()
    headers = rec.last.headers
    assert headers["authorization"] == "Bearer ap_test"
    assert headers["accept"] == "application/json"
    py = platform.python_version()
    assert headers["user-agent"] == f"anypost-python/{__version__} Python/{py}"


def test_content_type_only_with_body() -> None:
    client, rec = make_client(ok)
    client.whoami()  # GET, no body
    assert "content-type" not in rec.last.headers

    client.email.send({"from": "a@x.com", "to": ["b@y.com"], "text": "hi"})
    assert rec.last.headers["content-type"] == "application/json"


def test_extra_default_headers_are_sent() -> None:
    client, rec = make_client(ok, default_headers={"X-Tenant": "acme"})
    client.whoami()
    assert rec.last.headers["x-tenant"] == "acme"


def test_context_manager_closes() -> None:
    with make_client(ok)[0] as client:
        client.whoami()
    # closing twice must not raise
    client.close()

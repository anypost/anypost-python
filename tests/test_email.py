"""Send and batch-send: request shape, attachments, idempotency, 207."""

from __future__ import annotations

import base64

import httpx
from conftest import json_response, make_client

SENT = {"id": "email_018f4f3e", "created_at": "2026-04-30T12:00:00Z"}


def send_ok(_: httpx.Request) -> httpx.Response:
    return json_response(202, SENT)


def test_send_body_shape_and_from_key() -> None:
    client, rec = make_client(send_ok)
    result = client.email.send(
        {
            "from": "Acme <hello@example.com>",
            "to": ["alex@customer.com"],
            "subject": "Hi",
            "html": "<p>Hi</p>",
        }
    )
    assert result == SENT
    assert rec.last.url.path == "/v1/email"
    assert rec.last.method == "POST"
    body = rec.body()
    assert body["from"] == "Acme <hello@example.com>"
    assert body["to"] == ["alex@customer.com"]


def test_attachment_bytes_are_base64_encoded() -> None:
    client, rec = make_client(send_ok)
    client.email.send(
        {
            "from": "a@x.com",
            "to": ["b@y.com"],
            "subject": "s",
            "text": "t",
            "attachments": [{"filename": "f.bin", "content": b"\x00\x01\x02hello"}],
        }
    )
    att = rec.body()["attachments"][0]
    assert att["content"] == base64.b64encode(b"\x00\x01\x02hello").decode()
    assert att["filename"] == "f.bin"


def test_attachment_string_passes_through() -> None:
    client, rec = make_client(send_ok)
    client.email.send(
        {
            "from": "a@x.com",
            "to": ["b@y.com"],
            "text": "t",
            "attachments": [{"filename": "f.txt", "content": "YWxyZWFkeQ=="}],
        }
    )
    assert rec.body()["attachments"][0]["content"] == "YWxyZWFkeQ=="


def test_send_does_not_mutate_caller_dict() -> None:
    client, _ = make_client(send_ok)
    raw = b"bytes"
    params = {
        "from": "a@x.com",
        "to": ["b@y.com"],
        "text": "t",
        "attachments": [{"filename": "f", "content": raw}],
    }
    client.email.send(params)
    assert params["attachments"][0]["content"] is raw


def test_idempotency_key_passthrough() -> None:
    client, rec = make_client(send_ok)
    client.email.send(
        {"from": "a@x.com", "to": ["b@y.com"], "text": "t"},
        idempotency_key="my-key-123",
    )
    assert rec.last.headers["idempotency-key"] == "my-key-123"


def test_auto_idempotency_key_generated_for_sends() -> None:
    client, rec = make_client(send_ok)  # default max_retries=2 > 0
    client.email.send({"from": "a@x.com", "to": ["b@y.com"], "text": "t"})
    # A UUIDv4 is auto-generated so built-in retries cannot double-send.
    assert len(rec.last.headers["idempotency-key"]) == 36


def test_no_auto_key_when_retries_disabled() -> None:
    client, rec = make_client(send_ok, max_retries=0)
    client.email.send({"from": "a@x.com", "to": ["b@y.com"], "text": "t"})
    assert "idempotency-key" not in rec.last.headers


def test_batch_207_does_not_raise() -> None:
    payload = {
        "summary": {"total": 2, "queued": 1, "failed": 1},
        "data": [
            {"status": "queued", "index": 0, "id": "email_1", "created_at": "t"},
            {
                "status": "failed",
                "index": 1,
                "error": {"type": "permission_error", "message": "domain_not_verified"},
            },
        ],
    }
    client, rec = make_client(lambda r: json_response(207, payload))
    result = client.email.send_batch(
        {
            "emails": [
                {"from": "a@x.com", "to": ["b@y.com"], "subject": "s", "html": "h"},
                {"from": "a@x.com", "to": ["c@y.com"], "subject": "s", "html": "h"},
            ]
        }
    )
    assert result["summary"]["failed"] == 1
    assert result["data"][1]["status"] == "failed"
    assert rec.last.url.path == "/v1/email/batch"


def test_batch_defaults_attachments_encoded() -> None:
    client, rec = make_client(lambda r: json_response(202, {"summary": {}, "data": []}))
    client.email.send_batch(
        {
            "defaults": {
                "from": "a@x.com",
                "attachments": [{"filename": "shared", "content": b"xyz"}],
            },
            "emails": [{"to": ["b@y.com"], "subject": "s", "html": "h"}],
        }
    )
    body = rec.body()
    assert body["defaults"]["attachments"][0]["content"] == base64.b64encode(
        b"xyz"
    ).decode()

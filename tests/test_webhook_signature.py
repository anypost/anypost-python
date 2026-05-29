"""Webhook signature verification."""

from __future__ import annotations

import hashlib
import hmac

import pytest

from anypost import (
    WebhookVerificationError,
    unwrap_webhook_event,
    verify_webhook_signature,
)

SECRET = "whsec_testsecret"
PAYLOAD = '{"batch_id":"b_1","timestamp":1700000000,"events":[]}'
TS = 1700000000


def sign(secret: str, timestamp: int, body: str) -> str:
    return hmac.new(
        secret.encode(), f"{timestamp}.{body}".encode(), hashlib.sha256
    ).hexdigest()


def header(*sigs: str, t: int = TS) -> str:
    return ",".join([f"t={t}", *(f"v1={s}" for s in sigs)])


def test_valid_signature_passes() -> None:
    sig = sign(SECRET, TS, PAYLOAD)
    verify_webhook_signature(PAYLOAD, header(sig), SECRET, now=TS)


def test_accepts_bytes_payload() -> None:
    sig = sign(SECRET, TS, PAYLOAD)
    verify_webhook_signature(PAYLOAD.encode(), header(sig), SECRET, now=TS)


def test_multiple_v1_one_matches() -> None:
    good = sign(SECRET, TS, PAYLOAD)
    verify_webhook_signature(PAYLOAD, header("deadbeef", good), SECRET, now=TS)


def test_tampered_body_fails() -> None:
    sig = sign(SECRET, TS, PAYLOAD)
    with pytest.raises(WebhookVerificationError) as exc:
        verify_webhook_signature(PAYLOAD + "x", header(sig), SECRET, now=TS)
    assert exc.value.reason == "no_match"


def test_wrong_secret_fails() -> None:
    sig = sign("whsec_other", TS, PAYLOAD)
    with pytest.raises(WebhookVerificationError) as exc:
        verify_webhook_signature(PAYLOAD, header(sig), SECRET, now=TS)
    assert exc.value.reason == "no_match"


def test_timestamp_out_of_tolerance() -> None:
    sig = sign(SECRET, TS, PAYLOAD)
    with pytest.raises(WebhookVerificationError) as exc:
        verify_webhook_signature(PAYLOAD, header(sig), SECRET, now=TS + 1000)
    assert exc.value.reason == "timestamp_out_of_tolerance"


def test_tolerance_disabled_allows_old() -> None:
    sig = sign(SECRET, TS, PAYLOAD)
    verify_webhook_signature(
        PAYLOAD, header(sig), SECRET, now=TS + 100000, tolerance_seconds=0
    )


def test_malformed_header() -> None:
    with pytest.raises(WebhookVerificationError) as exc:
        verify_webhook_signature(PAYLOAD, "", SECRET, now=TS)
    assert exc.value.reason == "malformed_header"


def test_missing_timestamp() -> None:
    sig = sign(SECRET, TS, PAYLOAD)
    with pytest.raises(WebhookVerificationError) as exc:
        verify_webhook_signature(PAYLOAD, f"v1={sig}", SECRET, now=TS)
    assert exc.value.reason == "no_timestamp"


def test_missing_signature() -> None:
    with pytest.raises(WebhookVerificationError) as exc:
        verify_webhook_signature(PAYLOAD, f"t={TS}", SECRET, now=TS)
    assert exc.value.reason == "no_signatures"


def test_unwrap_returns_parsed_body() -> None:
    sig = sign(SECRET, TS, PAYLOAD)
    event = unwrap_webhook_event(PAYLOAD, header(sig), SECRET, now=TS)
    assert event["batch_id"] == "b_1"
    assert event["events"] == []

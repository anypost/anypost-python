"""Response-to-error mapping."""

from __future__ import annotations

import pytest
from conftest import json_response, make_client

from anypost import (
    APIError,
    AuthenticationError,
    ConflictError,
    IdempotencyMismatchError,
    NotFoundError,
    PayloadTooLargeError,
    PermissionError,
    RateLimitError,
    ValidationError,
)
from anypost._exceptions import AnypostError


def _send(client):
    return client.email.send({"from": "a@x.com", "to": ["b@y.com"], "text": "t"})


@pytest.mark.parametrize(
    "status,type_,cls",
    [
        (400, "validation_error", ValidationError),
        (401, "authentication_error", AuthenticationError),
        (403, "permission_error", PermissionError),
        (404, "not_found", NotFoundError),
        (409, "idempotency_concurrent", ConflictError),
        (422, "idempotency_mismatch", IdempotencyMismatchError),
        (429, "rate_limit_exceeded", RateLimitError),
        (500, "internal_error", APIError),
        (503, "provisioning_error", APIError),
    ],
)
def test_error_type_maps_to_class(status, type_, cls) -> None:
    body = {"error": {"type": type_, "message": "boom"}}
    client, _ = make_client(
        lambda r: json_response(status, body), max_retries=0
    )
    with pytest.raises(cls) as exc:
        _send(client)
    assert exc.value.type == type_
    assert exc.value.status == status
    assert exc.value.message == "boom"


def test_validation_errors_map_exposed() -> None:
    body = {
        "error": {
            "type": "validation_error",
            "message": "invalid",
            "errors": {"to": ["required"], "subject": ["too long"]},
        }
    }
    client, _ = make_client(lambda r: json_response(422, body), max_retries=0)
    with pytest.raises(ValidationError) as exc:
        _send(client)
    assert exc.value.errors == {"to": ["required"], "subject": ["too long"]}


def test_payload_too_large_flat_envelope() -> None:
    # 413 uses the flat shape: { "error": "payload_too_large" }.
    client, _ = make_client(
        lambda r: json_response(413, {"error": "payload_too_large"}), max_retries=0
    )
    with pytest.raises(PayloadTooLargeError) as exc:
        _send(client)
    assert exc.value.type == "payload_too_large"


def test_request_id_captured_from_header() -> None:
    client, _ = make_client(
        lambda r: json_response(
            404,
            {"error": {"type": "not_found", "message": "nope"}},
            headers={"Anypost-Request-Id": "req_abc123"},
        ),
        max_retries=0,
    )
    with pytest.raises(NotFoundError) as exc:
        client.domains.get("domain_x")
    assert exc.value.request_id == "req_abc123"


def test_rate_limit_exposes_retry_after() -> None:
    client, _ = make_client(
        lambda r: json_response(
            429,
            {"error": {"type": "rate_limit_exceeded", "message": "slow down"}},
            headers={"Retry-After": "7"},
        ),
        max_retries=0,
    )
    with pytest.raises(RateLimitError) as exc:
        _send(client)
    assert exc.value.retry_after == 7.0


def test_unknown_type_falls_back_to_status() -> None:
    client, _ = make_client(
        lambda r: json_response(403, {"error": {"type": "some_new_code"}}),
        max_retries=0,
    )
    with pytest.raises(PermissionError) as exc:
        _send(client)
    assert exc.value.type == "some_new_code"


def test_all_errors_subclass_base() -> None:
    client, _ = make_client(
        lambda r: json_response(500, {"error": {"type": "internal_error"}}),
        max_retries=0,
    )
    with pytest.raises(AnypostError):
        _send(client)

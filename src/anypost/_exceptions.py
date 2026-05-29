"""Error hierarchy and response-to-error mapping.

Every error raised by the SDK is an :class:`AnypostError`. Branch on
``err.type`` (the stable, machine-readable code) rather than on the HTTP
status or the message text.
"""

from __future__ import annotations

import email.utils
import time
from typing import Any, Mapping, Optional


class AnypostError(Exception):
    """Base class for every error raised by the SDK."""

    #: Stable, machine-readable error type. Branch on this.
    type: str
    #: HTTP status, or ``None`` when no response was received.
    status: Optional[int]
    #: Request id from the response, when present.
    request_id: Optional[str]
    #: The parsed response body (or underlying cause for connection errors).
    raw: Any

    def __init__(
        self,
        message: str,
        *,
        type: str,
        status: Optional[int] = None,
        request_id: Optional[str] = None,
        raw: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.type = type
        self.status = status
        self.request_id = request_id
        self.raw = raw


class ValidationError(AnypostError):
    """``400``/``422`` — the request body or query failed validation."""

    #: Field path -> list of problems. Present for ``validation_error``.
    errors: Mapping[str, list[str]]

    def __init__(
        self,
        message: str,
        *,
        errors: Optional[Mapping[str, list[str]]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.errors = errors or {}


class AuthenticationError(AnypostError):
    """``401`` — the API key is missing or invalid."""


class PermissionError(AnypostError):
    """``403`` — the key may not perform this action."""


class NotFoundError(AnypostError):
    """``404`` — no such resource for this team."""


class ConflictError(AnypostError):
    """``409`` — ``conflict``, ``idempotency_concurrent``, ``webhook_rotation_in_progress``."""


class IdempotencyMismatchError(AnypostError):
    """``422`` ``idempotency_mismatch`` — a key was reused with a different body."""


class RateLimitError(AnypostError):
    """``429`` — a rate limit was exceeded."""

    #: Parsed ``Retry-After``, in seconds, when the server sent one.
    retry_after: Optional[float]

    def __init__(
        self, message: str, *, retry_after: Optional[float] = None, **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class PayloadTooLargeError(AnypostError):
    """``413`` — the request body exceeded the 5 MB gateway limit."""


class APIError(AnypostError):
    """A server error (``5xx``), including ``internal_error`` and ``provisioning_error``."""


class APIConnectionError(AnypostError):
    """No HTTP response was received (network failure, timeout, or abort)."""

    def __init__(self, message: str, cause: Any = None) -> None:
        super().__init__(
            message, type="connection_error", status=None, request_id=None, raw=cause
        )
        self.__cause__ = cause if isinstance(cause, BaseException) else None


_REQUEST_ID_HEADERS = (
    "anypost-request-id",
    "x-anypost-request-id",
    "x-request-id",
)


def _read_request_id(headers: Mapping[str, str]) -> Optional[str]:
    for name in _REQUEST_ID_HEADERS:
        value = headers.get(name)
        if value:
            return value
    return None


def retry_after_seconds(headers: Mapping[str, str]) -> Optional[float]:
    """Parse a ``Retry-After`` header (delta-seconds or HTTP-date) into seconds."""
    value = headers.get("retry-after")
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    parsed = email.utils.parsedate_to_datetime(value)
    if parsed is None:
        return None
    return max(0.0, parsed.timestamp() - time.time())


def _type_from_status(status: int) -> str:
    return {
        400: "validation_error",
        401: "authentication_error",
        403: "permission_error",
        404: "not_found",
        409: "conflict",
        413: "payload_too_large",
        422: "validation_error",
        429: "rate_limit_exceeded",
    }.get(status, "internal_error" if status >= 500 else "api_error")


def _default_message(status: int) -> str:
    return f"Anypost request failed with status {status}."


def parse_error(
    status: int, body: Any, headers: Mapping[str, str]
) -> AnypostError:
    """Build the right :class:`AnypostError` subclass from an HTTP response."""
    request_id = _read_request_id(headers)
    envelope = body if isinstance(body, dict) else {}
    error = envelope.get("error")

    errors: dict[str, list[str]] = {}
    if isinstance(error, dict):
        # Canonical envelope: { error: { type, message, errors? } }.
        type_ = error.get("type") or _type_from_status(status)
        message = error.get("message") or _default_message(status)
        if isinstance(error.get("errors"), dict):
            errors = error["errors"]
    elif isinstance(error, str):
        # Flat envelope: { error: "<code>", message? }.
        type_ = error
        message = envelope.get("message") or error.replace("_", " ")
    else:
        type_ = _type_from_status(status)
        message = _default_message(status)

    common = dict(status=status, request_id=request_id, raw=body)

    if type_ == "validation_error":
        return ValidationError(message, errors=errors, type=type_, **common)
    if type_ == "authentication_error":
        return AuthenticationError(message, type=type_, **common)
    if type_ == "permission_error":
        return PermissionError(message, type=type_, **common)
    if type_ == "not_found":
        return NotFoundError(message, type=type_, **common)
    if type_ in ("conflict", "idempotency_concurrent", "webhook_rotation_in_progress"):
        return ConflictError(message, type=type_, **common)
    if type_ == "idempotency_mismatch":
        return IdempotencyMismatchError(message, type=type_, **common)
    if type_ == "rate_limit_exceeded":
        return RateLimitError(
            message, retry_after=retry_after_seconds(headers), type=type_, **common
        )
    if type_ == "payload_too_large":
        return PayloadTooLargeError(message, type=type_, **common)
    if type_ in ("provisioning_error", "internal_error"):
        return APIError(message, type=type_, **common)

    return _by_status(status, message, type_, errors, headers, common)


def _by_status(
    status: int,
    message: str,
    type_: str,
    errors: dict[str, list[str]],
    headers: Mapping[str, str],
    common: dict[str, Any],
) -> AnypostError:
    if status == 401:
        return AuthenticationError(message, type=type_, **common)
    if status == 403:
        return PermissionError(message, type=type_, **common)
    if status == 404:
        return NotFoundError(message, type=type_, **common)
    if status == 409:
        return ConflictError(message, type=type_, **common)
    if status == 413:
        return PayloadTooLargeError(message, type=type_, **common)
    if status == 429:
        return RateLimitError(
            message, retry_after=retry_after_seconds(headers), type=type_, **common
        )
    if status in (400, 422):
        return ValidationError(message, errors=errors, type=type_, **common)
    if status >= 500:
        return APIError(message, type=type_, **common)
    return AnypostError(message, type=type_, **common)

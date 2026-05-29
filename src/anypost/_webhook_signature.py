"""Verify the signature on an Anypost webhook delivery."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, List, Optional, Union

from typing_extensions import Literal, TypedDict

#: Why a signature failed to verify. Branch on this rather than the message.
#:
#: - ``malformed_header`` — the ``Anypost-Signature`` header could not be parsed.
#: - ``no_timestamp`` — the header carried no ``t=`` component.
#: - ``no_signatures`` — the header carried no ``v1=`` component.
#: - ``timestamp_out_of_tolerance`` — the delivery is older than the tolerance.
#: - ``no_match`` — no ``v1=`` component matched the computed signature.
WebhookVerificationFailure = Literal[
    "malformed_header",
    "no_timestamp",
    "no_signatures",
    "timestamp_out_of_tolerance",
    "no_match",
]

DEFAULT_TOLERANCE_SECONDS = 300


class WebhookVerificationError(Exception):
    """Raised when a webhook delivery's signature cannot be verified."""

    #: The machine-readable reason. Branch on this.
    reason: WebhookVerificationFailure

    def __init__(self, message: str, reason: WebhookVerificationFailure) -> None:
        super().__init__(message)
        self.reason = reason


class WebhookDeliveryEvent(TypedDict):
    """One event inside a :class:`WebhookDelivery`."""

    #: Unique event id. Stable across retries — de-duplicate on it.
    id: str
    type: str
    occurred_at: str
    #: Always carries ``email_id``; the rest depends on the event type.
    data: dict[str, Any]


class WebhookDelivery(TypedDict):
    """The outer envelope of a webhook delivery: one batch of one or more events."""

    #: Identifier for this batch. Stable across retries — de-duplicate on it.
    batch_id: str
    #: Unix timestamp the batch was signed with.
    timestamp: int
    events: List[WebhookDeliveryEvent]


def _to_text(payload: Union[str, bytes]) -> str:
    return payload if isinstance(payload, str) else payload.decode("utf-8")


def _parse_signature_header(header: str) -> tuple[int, List[str]]:
    if not header:
        raise WebhookVerificationError(
            "The Anypost-Signature header is empty.", "malformed_header"
        )

    timestamp: Optional[int] = None
    signatures: List[str] = []
    for part in header.split(","):
        key, sep, value = part.partition("=")
        if not sep:
            continue
        key = key.strip()
        value = value.strip()
        if key == "t":
            try:
                timestamp = int(value)
            except ValueError:
                continue
        elif key == "v1":
            signatures.append(value)

    if timestamp is None:
        raise WebhookVerificationError(
            "The Anypost-Signature header has no timestamp (t=).", "no_timestamp"
        )
    if not signatures:
        raise WebhookVerificationError(
            "The Anypost-Signature header has no v1= signature.", "no_signatures"
        )
    return timestamp, signatures


def _hmac_hex(secret: str, message: str) -> str:
    return hmac.new(
        secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def verify_webhook_signature(
    payload: Union[str, bytes],
    signature_header: str,
    secret: str,
    *,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    now: Optional[int] = None,
) -> None:
    """Verify an Anypost webhook signature.

    Pass the **raw** request body (the exact bytes received, before JSON
    parsing), the ``Anypost-Signature`` header value, and the webhook's signing
    secret. Returns on success; raises :class:`WebhookVerificationError`
    otherwise.

    The header may carry more than one ``v1=`` component during a secret
    rotation; a match on any one passes, so deliveries keep verifying across a
    rotation. Set ``tolerance_seconds=0`` to disable the freshness check.
    """
    timestamp, signatures = _parse_signature_header(signature_header)

    if tolerance_seconds > 0:
        current = now if now is not None else int(time.time())
        if current - timestamp > tolerance_seconds:
            raise WebhookVerificationError(
                f"Timestamp {timestamp} is older than the "
                f"{tolerance_seconds}s tolerance.",
                "timestamp_out_of_tolerance",
            )

    body = _to_text(payload)
    expected = _hmac_hex(secret, f"{timestamp}.{body}")

    # Constant-time over every candidate: accumulate without early exit.
    matched = False
    for candidate in signatures:
        if hmac.compare_digest(candidate, expected):
            matched = True
    if not matched:
        raise WebhookVerificationError(
            "No signature in the header matched the computed signature.",
            "no_match",
        )


def unwrap_webhook_event(
    payload: Union[str, bytes],
    signature_header: str,
    secret: str,
    *,
    tolerance_seconds: int = DEFAULT_TOLERANCE_SECONDS,
    now: Optional[int] = None,
) -> Any:
    """Verify a delivery and return its parsed JSON body.

    A thin wrapper over :func:`verify_webhook_signature` that runs
    ``json.loads`` only after the signature checks out.
    """
    verify_webhook_signature(
        payload,
        signature_header,
        secret,
        tolerance_seconds=tolerance_seconds,
        now=now,
    )
    return json.loads(_to_text(payload))

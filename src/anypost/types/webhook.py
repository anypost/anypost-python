"""Types for the ``/webhooks`` endpoints."""

from __future__ import annotations

from typing import List, Optional

from typing_extensions import Literal, TypedDict

#: An event type a webhook can subscribe to.
WebhookEventType = Literal[
    "email.sent",
    "email.delivered",
    "email.delayed",
    "email.bounced",
    "email.complained",
    "email.suppressed",
    "email.unsubscribed",
    "email.opened",
    "email.clicked",
]

#: A webhook's delivery state. ``active`` receives deliveries; ``disabled`` is
#: paused without losing config; ``circuit_disabled`` is server-managed after
#: repeated failures and clears on recovery. Only ``active`` and ``disabled``
#: can be set through the API.
WebhookStatus = Literal["active", "circuit_disabled", "disabled"]


class Webhook(TypedDict):
    """A webhook subscription. The signing secret is never returned here."""

    id: str
    name: str
    url: str
    events: List[WebhookEventType]
    status: WebhookStatus
    #: First 12 characters of the signing secret, for identification.
    signing_secret_prefix: str
    #: Prefix of the previous secret while a rotation grace window is open, else ``None``.
    signing_secret_previous_prefix: Optional[str]
    #: When the rotation grace window ends, or ``None`` if no rotation is in progress.
    signing_secret_grace_expires_at: Optional[str]
    last_delivery_at: Optional[str]
    created_at: str


class WebhookWithSecret(Webhook):
    """A webhook with its full signing secret. Returned only on create and rotate-secret."""

    #: The full signing secret (``whsec_...``). Returned once; store it securely.
    signing_secret: str


class WebhookTestResult(TypedDict):
    """The outcome of a synchronous test delivery. Never raised on a bad endpoint."""

    #: True only when the endpoint returned a 2xx status.
    delivered: bool
    #: HTTP status the endpoint returned, or ``None`` on a network failure.
    status_code: Optional[int]
    #: Wall-clock time from request start to response or error, in milliseconds.
    latency_ms: int
    #: A human-readable failure reason, or ``None`` on success.
    error: Optional[str]
    #: A truncated preview of the endpoint's response body, when available.
    response_body_preview: Optional[str]


class WebhookCreateParams(TypedDict):
    name: str
    #: An ``https://`` endpoint to receive signed deliveries.
    url: str
    #: At least one event type to subscribe to.
    events: List[WebhookEventType]


class WebhookUpdateParams(TypedDict):
    name: str
    url: str
    events: List[WebhookEventType]
    #: Set ``disabled`` to pause delivery, ``active`` to resume.
    status: Literal["active", "disabled"]

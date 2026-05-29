"""Official Python SDK for the Anypost email API."""

from __future__ import annotations

from ._async import AsyncAnypost
from ._client import Anypost
from ._exceptions import (
    AnypostError,
    APIConnectionError,
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
from ._pagination import AsyncPage, Page
from ._version import __version__
from ._webhook_signature import (
    WebhookDelivery,
    WebhookDeliveryEvent,
    WebhookVerificationError,
    WebhookVerificationFailure,
    unwrap_webhook_event,
    verify_webhook_signature,
)
from .resources import (
    ApiKeys,
    Domains,
    Email,
    Events,
    Identity,
    Suppressions,
    Templates,
    Webhooks,
)

__all__ = [
    "Anypost",
    "AsyncAnypost",
    "Page",
    "AsyncPage",
    "__version__",
    # Resources
    "ApiKeys",
    "Domains",
    "Email",
    "Events",
    "Identity",
    "Suppressions",
    "Templates",
    "Webhooks",
    # Errors
    "AnypostError",
    "APIConnectionError",
    "APIError",
    "AuthenticationError",
    "ConflictError",
    "IdempotencyMismatchError",
    "NotFoundError",
    "PayloadTooLargeError",
    "PermissionError",
    "RateLimitError",
    "ValidationError",
    # Webhooks
    "WebhookDelivery",
    "WebhookDeliveryEvent",
    "WebhookVerificationError",
    "WebhookVerificationFailure",
    "unwrap_webhook_event",
    "verify_webhook_signature",
]

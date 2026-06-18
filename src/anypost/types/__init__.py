"""Typed request and response shapes for the Anypost API."""

from __future__ import annotations

from .api_key import (
    ApiKey,
    ApiKeyCreateParams,
    ApiKeyUpdateParams,
    ApiKeyWithSecret,
)
from .common import (
    Attachment,
    HeaderMap,
    ListParams,
    Permissions,
    Tracking,
    Unsubscribe,
)
from .domain import (
    DnsRecord,
    Domain,
    DomainCreateParams,
    DomainTracking,
    DomainTrackingParams,
    DomainUpdateParams,
    VerificationFailure,
)
from .email import (
    BatchItemFailed,
    BatchItemQueued,
    BatchItemResult,
    BatchResponse,
    BatchSummary,
    EmailBatchDefaults,
    EmailBatchParams,
    EmailSendParams,
    SendResponse,
)
from .event import Event, EventBot, EventListParams, EventTracking, EventType
from .identity import WhoamiResponse
from .suppression import (
    Suppression,
    SuppressionCreateParams,
    SuppressionListParams,
    SuppressionOrigin,
    SuppressionReason,
)
from .template import (
    Template,
    TemplateCreateParams,
    TemplateDraft,
    TemplateDraftParams,
    TemplateDuplicateParams,
    TemplateKind,
    TemplateUpdateParams,
)
from .webhook import (
    Webhook,
    WebhookCreateParams,
    WebhookEventType,
    WebhookStatus,
    WebhookTestResult,
    WebhookUpdateParams,
    WebhookWithSecret,
)

__all__ = [
    "ApiKey",
    "ApiKeyCreateParams",
    "ApiKeyUpdateParams",
    "ApiKeyWithSecret",
    "Attachment",
    "HeaderMap",
    "ListParams",
    "Permissions",
    "Tracking",
    "Unsubscribe",
    "DnsRecord",
    "Domain",
    "DomainCreateParams",
    "DomainTracking",
    "DomainTrackingParams",
    "DomainUpdateParams",
    "VerificationFailure",
    "BatchItemFailed",
    "BatchItemQueued",
    "BatchItemResult",
    "BatchResponse",
    "BatchSummary",
    "EmailBatchDefaults",
    "EmailBatchParams",
    "EmailSendParams",
    "SendResponse",
    "Event",
    "EventBot",
    "EventListParams",
    "EventTracking",
    "EventType",
    "WhoamiResponse",
    "Suppression",
    "SuppressionCreateParams",
    "SuppressionListParams",
    "SuppressionOrigin",
    "SuppressionReason",
    "Template",
    "TemplateCreateParams",
    "TemplateDraft",
    "TemplateDraftParams",
    "TemplateDuplicateParams",
    "TemplateKind",
    "TemplateUpdateParams",
    "Webhook",
    "WebhookCreateParams",
    "WebhookEventType",
    "WebhookStatus",
    "WebhookTestResult",
    "WebhookUpdateParams",
    "WebhookWithSecret",
]

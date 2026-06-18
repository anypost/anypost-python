"""Types for the ``/events`` endpoint."""

from __future__ import annotations

from typing import List, Optional

from typing_extensions import Literal, TypedDict

from .common import ListParams

#: A customer-facing event type. The same set is emitted via webhooks;
#: operational events are never returned here.
EventType = Literal[
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


class EventBot(TypedDict):
    """Bot classification for a proxied open or click.

    Pure-noise machine traffic (mailbox prefetchers, scanners) never becomes
    an event, so the only kind a customer ever sees is ``proxy`` — a real open
    whose origin is anonymized by a mailbox image proxy (Gmail, Yahoo, etc.).
    """

    #: The detected mailbox image proxy, e.g. ``google``, ``yahoo``, ``bing``.
    source: str
    #: Always ``proxy`` on customer-visible events.
    kind: Literal["proxy"]


class EventTracking(TypedDict, total=False):
    """Tracking metadata on ``email.opened`` / ``email.clicked`` events.

    Mirrors the webhook payload's ``data.tracking``. Carries ``bot`` only when
    the interaction came from a mailbox image proxy; a human open/click has no
    ``bot``.
    """

    bot: EventBot


#: A single email-pipeline event for the team.
#:
#: Every field is always present; fields that don't apply to a given event
#: type are ``None`` rather than absent. The ``"from"`` key mirrors the wire
#: shape (accessed as ``event["from"]``).
Event = TypedDict(
    "Event",
    {
        # Stable id for log correlation. Not addressable.
        "id": str,
        "type": EventType,
        # ISO 8601 UTC timestamp of when the event was observed.
        "occurred_at": str,
        # The email_<uuidv7> id minted when the message was accepted.
        "email_id": Optional[str],
        # The RFC 5322 Message-ID: header, when a relaying server stamped one.
        "message_id": Optional[str],
        # The envelope From: address.
        "from": Optional[str],
        # The From: domain, lowercased.
        "from_domain": Optional[str],
        # The single recipient this event refers to.
        "recipient": Optional[str],
        # The captured Subject: header, truncated at the capture limit.
        "subject": Optional[str],
        # The originating send's campaign value.
        "campaign": Optional[str],
        # Public id of the template the originating send used.
        "template_id": Optional[str],
        # Send-time topic the message was tagged with.
        "topic": Optional[str],
        # Customer-supplied tags from the originating send. Empty list when none.
        "tags": List[str],
        # SMTP reply code observed. None without an SMTP exchange.
        "smtp_code": Optional[int],
        # Bounce type (e.g. Hard, Soft). Only on email.bounced.
        "bounce_type": Optional[str],
        # Bounce classification (e.g. InvalidRecipient). Only on email.bounced.
        "bounce_classification": Optional[str],
        # Delivery attempt number for this recipient. None for non-delivery events.
        "attempt": Optional[int],
        # Tracking metadata, mirroring the webhook payload's data.tracking. None
        # on every event except opens/clicks, and on human opens/clicks. Carries
        # bot when the open/click came from a mailbox image proxy.
        "tracking": Optional[EventTracking],
    },
)


class EventListParams(ListParams, total=False):
    """Query parameters for ``events.list``.

    The window defaults to the last 24 hours and is clamped to the plan's
    retention. All filters are exact-match except ``tags``.
    """

    #: ISO 8601 start of the window (inclusive). Defaults to 24h before ``end``.
    start: str
    #: ISO 8601 end of the window (exclusive). Defaults to now.
    end: str
    #: Restrict to one event type.
    event_type: EventType
    #: Exact recipient address (lowercased server-side).
    recipient: str
    #: Restrict to one message's ``email_<uuidv7>`` id.
    email_id: str
    #: Exact ``Message-ID:`` header match.
    message_id: str
    #: Sending domain hostname (not the ``domain_<uuid>`` id). Unknown domains return ``400``.
    domain: str
    #: Send-time topic.
    topic: str
    #: Send-time ``campaign`` value. Case-sensitive exact match.
    campaign: str
    #: Template the originating send used.
    template_id: str
    #: Restrict to events carrying any of these tags (``hasAny``). Up to 10.
    tags: List[str]

"""Types for the ``/suppressions`` endpoints."""

from __future__ import annotations

from typing import List, Optional

from typing_extensions import Literal, NotRequired, TypedDict

from .common import ListParams

#: Why an address is suppressed.
SuppressionReason = Literal[
    "permanent_bounce", "complaint", "unsubscribed", "manual"
]

#: Provenance of a suppression row.
SuppressionOrigin = Literal["auto", "manual"]


class Suppression(TypedDict):
    """A suppressed recipient address, scoped to a topic."""

    #: ``sup_``-prefixed id. Lookups/deletes key on ``(email, topic)``.
    id: str
    #: The suppressed address, normalized to lowercase.
    email: str
    #: The topic this suppression applies to. ``*`` means every topic.
    topic: str
    reason: SuppressionReason
    origin: SuppressionOrigin
    #: Bounce classification or ARF feedback-type. ``None`` for manual entries.
    classification: Optional[str]
    #: SMTP reply code from the bounce. ``None`` for complaints and manual entries.
    smtp_code: Optional[int]
    #: Free-form note attached at creation.
    note: Optional[str]
    #: When the suppression was first observed.
    suppressed_at: str
    #: Always ``None``: suppressions do not expire. Kept for compatibility and
    #: will be removed in a future major version.
    expires_at: Optional[str]
    created_at: str


class SuppressionListParams(ListParams, total=False):
    """Query parameters for ``suppressions.list``."""

    #: Case-insensitive substring match against the address.
    email_contains: str
    #: Restrict to a topic. ``*`` for global entries, or a specific topic name.
    topic: str
    reason: SuppressionReason
    origin: SuppressionOrigin


class SuppressionCreateParams(TypedDict):
    """Body for ``suppressions.create``."""

    email: str
    #: Topic to scope the suppression. Omit or ``*`` to block every topic.
    topic: NotRequired[str]
    #: Optional internal annotation, preserved across automatic re-suppressions.
    note: NotRequired[Optional[str]]


class SuppressionBatchItem(TypedDict):
    """One entry in a ``suppressions.create_batch`` call."""

    email: str
    #: Topic to scope the suppression. Omit for ``*`` (every topic).
    topic: NotRequired[str]
    #: Free-form. ``permanent_bounce``, ``complaint``, ``unsubscribed``, and
    #: ``manual`` are recognized, as are common aliases such as ``bounce``,
    #: ``hard bounce``, ``spam report``, and ``opt-out`` (case and punctuation
    #: ignored). Anything else records ``manual``.
    reason: NotRequired[str]
    #: Optional internal annotation (max 2000 characters).
    note: NotRequired[Optional[str]]


class SuppressionBatchInvalid(TypedDict):
    """An item in a batch whose email is not a valid address."""

    #: Position in the request array, 0-based.
    index: int
    email: Optional[str]


class SuppressionBatchResult(TypedDict):
    """Response from ``POST /suppressions/batch``.

    ``imported + already_suppressed + len(invalid)`` equals the items sent.
    """

    #: Suppressions this call created.
    imported: int
    #: Items whose address and topic were already suppressed, including repeats
    #: within the batch. Left unchanged.
    already_suppressed: int
    invalid: List[SuppressionBatchInvalid]

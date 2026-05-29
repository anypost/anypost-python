"""Types for the ``/email`` and ``/email/batch`` endpoints.

These mirror the JSON wire shape exactly, so a params dict reads the same as
the documented request body — including the ``"from"`` key, which a Python
``dict`` literal accepts even though ``from`` is a reserved word.
"""

from __future__ import annotations

from typing import Any, Dict, List, Union

from typing_extensions import Literal, NotRequired, Required, TypedDict

from .common import Attachment, HeaderMap, Tracking, Unsubscribe

#: A single message to send.
#:
#: At least one of ``text``, ``html``, or ``template_id`` is required;
#: ``template_id`` cannot be combined with inline ``text``/``html``. When
#: ``unsubscribe["mode"]`` is ``"generate"``, ``topic`` is also required.
EmailSendParams = TypedDict(
    "EmailSendParams",
    {
        # Sender on a verified domain. Bare or "Display Name <addr@host>".
        "from": Required[str],
        # 1-50 primary recipients. Combined to + cc + bcc must be <= 50.
        "to": Required[List[str]],
        "cc": List[str],
        "bcc": List[str],
        # One address or up to 10.
        "reply_to": Union[str, List[str]],
        # Required unless a referenced template supplies it.
        "subject": str,
        "text": str,
        "html": str,
        # Reference to a published template (template_<uuid>).
        "template_id": str,
        "headers": HeaderMap,
        # Up to 20 inline attachments.
        "attachments": List[Attachment],
        # Up to 10 free-form labels ([A-Za-z0-9_-]{1,64}).
        "tags": List[str],
        # Stream-segmentation label ([A-Za-z0-9_-]{1,64}).
        "campaign": str,
        # Suppression scope / topic bucket ([a-z0-9_.-]{1,64}).
        "topic": str,
        "tracking": Tracking,
        # Handlebars substitution map. Encoded JSON must be <= 64 KB.
        "variables": Dict[str, Any],
        "unsubscribe": Unsubscribe,
    },
    total=False,
)

#: Batch-wide defaults, applied to every entry that does not set its own value.
#: ``to`` is excluded — recipients are always per-entry. Scalars override,
#: lists concatenate; see the API docs for the per-field merge semantics.
EmailBatchDefaults = TypedDict(
    "EmailBatchDefaults",
    {
        "from": str,
        "cc": List[str],
        "bcc": List[str],
        "reply_to": Union[str, List[str]],
        "subject": str,
        "text": str,
        "html": str,
        "template_id": str,
        "headers": HeaderMap,
        "attachments": List[Attachment],
        "tags": List[str],
        "campaign": str,
        "topic": str,
        "tracking": Tracking,
        "variables": Dict[str, Any],
        "unsubscribe": Unsubscribe,
    },
    total=False,
)


class EmailBatchParams(TypedDict):
    """Body for ``POST /email/batch``. 1-100 messages."""

    emails: List[EmailSendParams]
    defaults: NotRequired[EmailBatchDefaults]


class SendResponse(TypedDict):
    """Response from a successful single send (``202``)."""

    #: Public message identifier (``email_<uuidv7>``).
    id: str
    created_at: str


class BatchItemQueued(TypedDict):
    status: Literal["queued"]
    #: Zero-based position in the request ``emails`` array.
    index: int
    id: str
    created_at: str


class BatchItemError(TypedDict):
    type: Literal["validation_error", "permission_error", "internal_error"]
    message: str


class BatchItemFailed(TypedDict):
    status: Literal["failed"]
    index: int
    #: Inner canonical error: ``{ type, message }``, no wrapping ``error`` key.
    error: BatchItemError


#: Per-entry outcome of a batch send. Discriminated by ``status``.
BatchItemResult = Union[BatchItemQueued, BatchItemFailed]


class BatchSummary(TypedDict):
    total: int
    queued: int
    failed: int


class BatchResponse(TypedDict):
    """Response from ``POST /email/batch``.

    A ``207`` (mixed outcomes) is a success, not an error: inspect each
    entry's ``status``. ``data[i]["index"] == i``.
    """

    summary: BatchSummary
    data: List[BatchItemResult]

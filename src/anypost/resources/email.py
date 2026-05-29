"""The ``/email`` resource: single and batch sends."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from .._base64 import bytes_to_base64
from .._http import HttpClient
from ..types.email import BatchResponse, EmailBatchParams, EmailSendParams, SendResponse


def _encode_attachments(message: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of a message with byte-valued attachment ``content``
    base64-encoded. A ``str`` content is already encoded and passes through.
    """
    out = dict(message)
    attachments = out.get("attachments")
    if not attachments:
        return out
    out["attachments"] = [
        att
        if isinstance(att.get("content"), str)
        else {**att, "content": bytes_to_base64(att["content"])}
        for att in attachments
    ]
    return out


class Email:
    """Operations on the ``/email`` endpoints."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def send(
        self,
        email: EmailSendParams,
        *,
        idempotency_key: Optional[str] = None,
    ) -> SendResponse:
        """Send a single message.

        All addresses in ``to``/``cc``/``bcc`` share one envelope. Returns the
        queued message id; raises an :class:`~anypost.AnypostError` subclass on
        failure.
        """
        return self._http.request(
            "POST",
            "/email",
            body=_encode_attachments(email),
            idempotent=True,
            idempotency_key=idempotency_key,
        )

    def send_batch(
        self,
        batch: EmailBatchParams,
        *,
        idempotency_key: Optional[str] = None,
    ) -> BatchResponse:
        """Send 1-100 independent messages in one request.

        A mixed-outcome batch (HTTP ``207``) returns normally — inspect each
        entry's ``status`` in ``data``; it does not raise.
        """
        body: dict[str, Any] = dict(batch)
        if batch.get("defaults"):
            body["defaults"] = _encode_attachments(batch["defaults"])
        body["emails"] = [_encode_attachments(e) for e in batch["emails"]]
        return self._http.request(
            "POST",
            "/email/batch",
            body=body,
            idempotent=True,
            idempotency_key=idempotency_key,
        )

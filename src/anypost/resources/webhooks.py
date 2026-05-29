"""The ``/webhooks`` resource."""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote

from .._http import HttpClient
from .._pagination import Page
from ..types.common import ListParams
from ..types.webhook import (
    Webhook,
    WebhookCreateParams,
    WebhookTestResult,
    WebhookUpdateParams,
    WebhookWithSecret,
)


class Webhooks:
    """Operations on the ``/webhooks`` endpoints."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self, params: Optional[ListParams] = None) -> Page[Webhook]:
        """List the team's webhooks, newest-first."""
        return self._fetch_page(params)

    def create(self, params: WebhookCreateParams) -> WebhookWithSecret:
        """Create a webhook.

        The full ``signing_secret`` is on the response to this call only —
        store it now to verify future deliveries; later reads return only the
        prefix.
        """
        return self._http.request("POST", "/webhooks", body=params)

    def get(self, id: str) -> Webhook:
        """Retrieve a webhook. The signing secret is never returned — only its prefix."""
        return self._http.request("GET", f"/webhooks/{quote(id, safe='')}")

    def update(self, id: str, params: WebhookUpdateParams) -> Webhook:
        """Update a webhook's name, URL, subscribed events, and status.

        This does not rotate the signing secret — use :meth:`rotate_secret`.
        """
        return self._http.request("PATCH", f"/webhooks/{quote(id, safe='')}", body=params)

    def delete(self, id: str) -> None:
        """Permanently delete a webhook."""
        self._http.request("DELETE", f"/webhooks/{quote(id, safe='')}")

    def test(self, id: str) -> WebhookTestResult:
        """Send one synthetic ``webhook.test`` event and report the outcome.

        One-shot, not retried, and absent from delivery history. Returns the
        result even when the endpoint fails — read ``delivered`` and
        ``status_code``. Works on a ``disabled`` webhook too.
        """
        return self._http.request("POST", f"/webhooks/{quote(id, safe='')}/test")

    def rotate_secret(self, id: str) -> WebhookWithSecret:
        """Rotate the signing secret.

        The new secret is on this response only. The previous secret stays
        valid for a 24h grace window, during which deliveries carry a ``v1=``
        component for each. Rotating again before the window ends raises
        ``webhook_rotation_in_progress`` (a :class:`~anypost.ConflictError`).
        """
        return self._http.request("POST", f"/webhooks/{quote(id, safe='')}/rotate-secret")

    def _fetch_page(self, params: Optional[ListParams]) -> Page[Webhook]:
        params = params or {}
        response = self._http.request(
            "GET",
            "/webhooks",
            query={"limit": params.get("limit"), "after": params.get("after")},
        )
        return Page(
            response, lambda after: self._fetch_page({**params, "after": after})
        )

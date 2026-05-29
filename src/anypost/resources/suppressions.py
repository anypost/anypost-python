"""The ``/suppressions`` resource. Entries key on ``(email, topic)``."""

from __future__ import annotations

from typing import List, Optional
from urllib.parse import quote

from .._http import HttpClient
from .._pagination import Page
from ..types.suppression import (
    Suppression,
    SuppressionCreateParams,
    SuppressionListParams,
)


class Suppressions:
    """Operations on the ``/suppressions`` endpoints."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(
        self, params: Optional[SuppressionListParams] = None
    ) -> Page[Suppression]:
        """List the team's suppressions, newest-first. Expired rows are filtered out.

        Filter with ``email_contains``, ``topic``, ``reason``, and ``origin``.
        """
        return self._fetch_page(params)

    def create(self, params: SuppressionCreateParams) -> Suppression:
        """Add a manual suppression.

        Defaults to topic ``*`` (every topic). Raises ``validation_error`` if
        an active entry for the same ``(email, topic)`` exists.
        """
        return self._http.request("POST", "/suppressions", body=params)

    def get(self, email: str, topic: str) -> Suppression:
        """Retrieve the suppression for an ``(email, topic)`` pair.

        Use ``*`` as the topic for the global row. Raises ``not_found`` if the
        pair isn't suppressed.
        """
        return self._http.request(
            "GET", f"/suppressions/{quote(email, safe='')}/{quote(topic, safe='')}"
        )

    def delete(self, email: str, topic: str) -> None:
        """Remove the single ``(email, topic)`` row. Other topics are untouched."""
        self._http.request(
            "DELETE", f"/suppressions/{quote(email, safe='')}/{quote(topic, safe='')}"
        )

    def list_for_email(self, email: str) -> List[Suppression]:
        """List every suppression on file for an address, across all topics.

        Raises ``not_found`` if the address has no active suppressions.
        """
        response = self._http.request("GET", f"/suppressions/{quote(email, safe='')}")
        return response["data"]

    def delete_for_email(self, email: str) -> None:
        """Remove an address from the suppression list across every topic."""
        self._http.request("DELETE", f"/suppressions/{quote(email, safe='')}")

    def _fetch_page(
        self, params: Optional[SuppressionListParams]
    ) -> Page[Suppression]:
        params = params or {}
        response = self._http.request(
            "GET",
            "/suppressions",
            query={
                "limit": params.get("limit"),
                "after": params.get("after"),
                "email_contains": params.get("email_contains"),
                "topic": params.get("topic"),
                "reason": params.get("reason"),
                "origin": params.get("origin"),
            },
        )
        return Page(
            response, lambda after: self._fetch_page({**params, "after": after})
        )

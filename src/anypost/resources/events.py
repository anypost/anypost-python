"""The ``/events`` resource. List-only — events are not addressable by id."""

from __future__ import annotations

from typing import Optional

from .._http import HttpClient
from .._pagination import Page
from ..types.event import Event, EventListParams


class Events:
    """Read access to the ``/events`` stream."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self, params: Optional[EventListParams] = None) -> Page[Event]:
        """Page through the team's events, newest-first.

        The window defaults to the last 24 hours and is clamped to the plan's
        retention. Filter with ``start``, ``end``, ``event_type``,
        ``recipient``, ``email_id``, ``message_id``, ``domain``, ``topic``,
        ``campaign``, ``template_id``, and ``tags``.
        """
        return self._fetch_page(params)

    def _fetch_page(self, params: Optional[EventListParams]) -> Page[Event]:
        params = params or {}
        tags = params.get("tags")
        response = self._http.request(
            "GET",
            "/events",
            query={
                "limit": params.get("limit"),
                "after": params.get("after"),
                "start": params.get("start"),
                "end": params.get("end"),
                "event_type": params.get("event_type"),
                "recipient": params.get("recipient"),
                "email_id": params.get("email_id"),
                "message_id": params.get("message_id"),
                "domain": params.get("domain"),
                "topic": params.get("topic"),
                "campaign": params.get("campaign"),
                "template_id": params.get("template_id"),
                # Sent comma-separated (tags=a,b); the API matches with hasAny.
                "tags": ",".join(tags) if tags else None,
            },
        )
        return Page(
            response, lambda after: self._fetch_page({**params, "after": after})
        )

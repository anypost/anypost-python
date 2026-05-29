"""The ``/domains`` resource."""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote

from .._http import HttpClient
from .._pagination import Page
from ..types.common import ListParams
from ..types.domain import Domain, DomainCreateParams, DomainUpdateParams


class Domains:
    """Operations on the ``/domains`` endpoints."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self, params: Optional[ListParams] = None) -> Page[Domain]:
        """List the team's domains, newest-first.

        Returns one :class:`~anypost.Page`; iterate it to walk every page, or
        follow ``page.next_cursor`` yourself.
        """
        return self._fetch_page(params)

    def create(self, params: DomainCreateParams) -> Domain:
        """Add a sending domain. The returned domain is ``pending`` until verified."""
        return self._http.request("POST", "/domains", body=params)

    def get(self, id: str) -> Domain:
        """Retrieve a single domain by id."""
        return self._http.request("GET", f"/domains/{quote(id, safe='')}")

    def update(self, id: str, params: DomainUpdateParams) -> Domain:
        """Update a domain's tracking configuration. The domain ``name`` is immutable."""
        return self._http.request("PATCH", f"/domains/{quote(id, safe='')}", body=params)

    def delete(self, id: str) -> None:
        """Permanently delete a domain and its DKIM keys."""
        self._http.request("DELETE", f"/domains/{quote(id, safe='')}")

    def verify(self, id: str) -> Domain:
        """Trigger a verification check.

        Always returns the current domain — read ``status`` and
        ``verification_failure`` to learn the outcome; a still-``pending``
        domain does not raise. Safe to poll while DNS propagates.
        """
        return self._http.request("POST", f"/domains/{quote(id, safe='')}/verify")

    def _fetch_page(self, params: Optional[ListParams]) -> Page[Domain]:
        params = params or {}
        response = self._http.request(
            "GET",
            "/domains",
            query={"limit": params.get("limit"), "after": params.get("after")},
        )
        return Page(
            response, lambda after: self._fetch_page({**params, "after": after})
        )

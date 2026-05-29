"""The ``/api-keys`` resource."""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote

from .._http import HttpClient
from .._pagination import Page
from ..types.api_key import (
    ApiKey,
    ApiKeyCreateParams,
    ApiKeyUpdateParams,
    ApiKeyWithSecret,
)
from ..types.common import ListParams


class ApiKeys:
    """Operations on the ``/api-keys`` endpoints."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self, params: Optional[ListParams] = None) -> Page[ApiKey]:
        """List the team's API keys, newest-first."""
        return self._fetch_page(params)

    def create(self, params: ApiKeyCreateParams) -> ApiKeyWithSecret:
        """Issue a new API key.

        The plaintext secret is returned only in this response, as ``key`` —
        store it securely; it cannot be retrieved later.
        """
        return self._http.request("POST", "/api-keys", body=params)

    def get(self, id: str) -> ApiKey:
        """Retrieve a single API key's metadata. The secret is never returned."""
        return self._http.request("GET", f"/api-keys/{quote(id, safe='')}")

    def update(self, id: str, params: ApiKeyUpdateParams) -> ApiKey:
        """Update a key's name, permissions, and restrictions.

        The secret is not rotated here. Changes may take up to 5 minutes to
        propagate through the gateway cache.
        """
        return self._http.request("PATCH", f"/api-keys/{quote(id, safe='')}", body=params)

    def delete(self, id: str) -> None:
        """Delete a key. It may keep authenticating for up to 5 minutes (gateway cache)."""
        self._http.request("DELETE", f"/api-keys/{quote(id, safe='')}")

    def _fetch_page(self, params: Optional[ListParams]) -> Page[ApiKey]:
        params = params or {}
        response = self._http.request(
            "GET",
            "/api-keys",
            query={"limit": params.get("limit"), "after": params.get("after")},
        )
        return Page(
            response, lambda after: self._fetch_page({**params, "after": after})
        )

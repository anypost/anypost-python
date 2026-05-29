"""Identity operations (``/whoami``)."""

from __future__ import annotations

from .._http import HttpClient
from ..types.identity import WhoamiResponse


class Identity:
    """Identity operations."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def whoami(self) -> WhoamiResponse:
        """Identify the team and permission level behind the current API key."""
        return self._http.request("GET", "/whoami")

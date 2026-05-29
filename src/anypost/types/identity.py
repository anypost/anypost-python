"""Types for the ``/whoami`` endpoint."""

from __future__ import annotations

from typing import Optional

from typing_extensions import TypedDict

from .common import Permissions


class WhoamiTeam(TypedDict):
    id: str
    name: str


class WhoamiApiKey(TypedDict):
    id: str
    permissions: Permissions


class WhoamiResponse(TypedDict):
    """The identity resolved from the API key on the request."""

    #: The team the key belongs to, or ``None`` if it could not be resolved.
    team: Optional[WhoamiTeam]
    api_key: WhoamiApiKey

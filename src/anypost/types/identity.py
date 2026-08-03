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


class WhoamiLimits(TypedDict):
    """The sending limits currently enforced against a team.

    These are effective values and can differ from the plan defaults, so read
    them at runtime rather than hardcoding them.
    """

    #: Messages the team may send per calendar day (UTC). Exceeding it returns
    #: 429 with scope ``daily``.
    daily: int
    #: Messages the team may send per billing month. Exceeding it returns 429
    #: with scope ``monthly``, unless prepaid overage credits cover the excess;
    #: those are not counted here.
    monthly: int
    #: How fast accepted mail is released to receiving servers. Not a request
    #: limit and never a rejection: mail beyond this rate queues and drains at
    #: the metered rate.
    delivery_rate_per_minute: int


class WhoamiResponse(TypedDict):
    """The identity resolved from the API key on the request."""

    #: The team the key belongs to, or ``None`` if it could not be resolved.
    team: Optional[WhoamiTeam]
    api_key: WhoamiApiKey
    #: The limits in force for the team, or ``None`` if it could not be resolved.
    limits: Optional[WhoamiLimits]

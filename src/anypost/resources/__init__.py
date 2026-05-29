"""Resource clients, one per API path."""

from __future__ import annotations

from .api_keys import ApiKeys
from .domains import Domains
from .email import Email
from .events import Events
from .identity import Identity
from .suppressions import Suppressions
from .templates import Templates
from .webhooks import Webhooks

__all__ = [
    "ApiKeys",
    "Domains",
    "Email",
    "Events",
    "Identity",
    "Suppressions",
    "Templates",
    "Webhooks",
]

"""The synchronous :class:`Anypost` client."""

from __future__ import annotations

import os
from types import TracebackType
from typing import Mapping, Optional, Type

import httpx

from ._http import HttpClient
from .resources.api_keys import ApiKeys
from .resources.domains import Domains
from .resources.email import Email
from .resources.events import Events
from .resources.identity import Identity
from .resources.suppressions import Suppressions
from .resources.templates import Templates
from .resources.webhooks import Webhooks
from .types.identity import WhoamiResponse

DEFAULT_BASE_URL = "https://api.anypost.com/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2


class Anypost:
    """Client for the Anypost email API.

    ::

        from anypost import Anypost

        client = Anypost("ap_your_api_key")        # or Anypost() to read ANYPOST_API_KEY
        result = client.email.send({
            "from": "Acme <you@yourdomain.com>",
            "to": ["someone@example.com"],
            "subject": "Hello",
            "html": "<p>It worked.</p>",
        })
    """

    #: Send operations (``/email``, ``/email/batch``).
    email: Email
    #: Sending-domain operations (``/domains``).
    domains: Domains
    #: API-key operations (``/api-keys``).
    api_keys: ApiKeys
    #: Template operations (``/templates``), including the draft/publish flow.
    templates: Templates
    #: Suppression-list operations (``/suppressions``).
    suppressions: Suppressions
    #: Webhook operations (``/webhooks``), including test and secret rotation.
    webhooks: Webhooks
    #: Read access to the event stream (``/events``).
    events: Events

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        http_client: Optional[httpx.Client] = None,
    ) -> None:
        key = api_key or os.environ.get("ANYPOST_API_KEY")
        if not key:
            raise ValueError(
                "An Anypost API key is required. Pass it to the constructor "
                "or set ANYPOST_API_KEY."
            )

        self._http = HttpClient(
            api_key=key,
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers or {},
            client=http_client,
        )
        self._identity = Identity(self._http)

        self.email = Email(self._http)
        self.domains = Domains(self._http)
        self.api_keys = ApiKeys(self._http)
        self.templates = Templates(self._http)
        self.suppressions = Suppressions(self._http)
        self.webhooks = Webhooks(self._http)
        self.events = Events(self._http)

    def whoami(self) -> WhoamiResponse:
        """Identify the team and permission level behind the current API key."""
        return self._identity.whoami()

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._http.close()

    def __enter__(self) -> "Anypost":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.close()

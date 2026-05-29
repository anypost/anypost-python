"""The asynchronous :class:`AsyncAnypost` client."""

from __future__ import annotations

import os
from types import TracebackType
from typing import Mapping, Optional, Type

import httpx

from .._async_http import AsyncHttpClient
from ..types.identity import WhoamiResponse
from .resources import (
    AsyncApiKeys,
    AsyncDomains,
    AsyncEmail,
    AsyncEvents,
    AsyncIdentity,
    AsyncSuppressions,
    AsyncTemplates,
    AsyncWebhooks,
)

DEFAULT_BASE_URL = "https://api.anypost.com/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2


class AsyncAnypost:
    """Async client for the Anypost email API.

    ::

        import asyncio
        from anypost import AsyncAnypost

        async def main():
            async with AsyncAnypost("ap_your_api_key") as client:
                result = await client.email.send({
                    "from": "Acme <you@yourdomain.com>",
                    "to": ["someone@example.com"],
                    "subject": "Hello",
                    "html": "<p>It worked.</p>",
                })

        asyncio.run(main())
    """

    email: AsyncEmail
    domains: AsyncDomains
    api_keys: AsyncApiKeys
    templates: AsyncTemplates
    suppressions: AsyncSuppressions
    webhooks: AsyncWebhooks
    events: AsyncEvents

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        key = api_key or os.environ.get("ANYPOST_API_KEY")
        if not key:
            raise ValueError(
                "An Anypost API key is required. Pass it to the constructor "
                "or set ANYPOST_API_KEY."
            )

        self._http = AsyncHttpClient(
            api_key=key,
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            max_retries=max_retries,
            default_headers=default_headers or {},
            client=http_client,
        )
        self._identity = AsyncIdentity(self._http)

        self.email = AsyncEmail(self._http)
        self.domains = AsyncDomains(self._http)
        self.api_keys = AsyncApiKeys(self._http)
        self.templates = AsyncTemplates(self._http)
        self.suppressions = AsyncSuppressions(self._http)
        self.webhooks = AsyncWebhooks(self._http)
        self.events = AsyncEvents(self._http)

    async def whoami(self) -> WhoamiResponse:
        """Identify the team and permission level behind the current API key."""
        return await self._identity.whoami()

    async def aclose(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncAnypost":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        await self.aclose()

"""Asynchronous HTTP transport. Mirrors :mod:`anypost._http`, sharing its
pure helpers (header building, backoff, decoding)."""

from __future__ import annotations

import asyncio
from typing import Any, Mapping, Optional

import httpx

from ._exceptions import APIConnectionError, parse_error
from ._http import (
    RETRYABLE_STATUS,
    QueryValue,
    backoff_seconds,
    build_headers,
    clean_query,
    connection_message,
    decode_body,
)


class AsyncHttpClient:
    """Owns an :class:`httpx.AsyncClient` and implements the async request loop."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: float,
        max_retries: int,
        default_headers: Mapping[str, str],
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._api_key = api_key
        self._max_retries = max_retries
        self._default_headers = dict(default_headers)
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(base_url=base_url, timeout=timeout)

    async def request(
        self,
        method: str,
        path: str,
        *,
        body: Any = None,
        query: Optional[Mapping[str, QueryValue]] = None,
        idempotent: bool = False,
        idempotency_key: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        extra_headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        retries = self._max_retries if max_retries is None else max_retries
        headers = build_headers(
            self._api_key,
            self._default_headers,
            has_body=body is not None,
            idempotent=idempotent,
            idempotency_key=idempotency_key,
            max_retries=retries,
            extra_headers=extra_headers,
        )
        kwargs: dict[str, Any] = {"headers": headers, "params": clean_query(query)}
        if body is not None:
            kwargs["json"] = body
        if timeout is not None:
            kwargs["timeout"] = timeout

        attempt = 0
        while True:
            try:
                response = await self._client.request(method, path, **kwargs)
            except httpx.RequestError as exc:
                if attempt < retries:
                    await asyncio.sleep(backoff_seconds(attempt, None))
                    attempt += 1
                    continue
                raise APIConnectionError(connection_message(exc), exc) from exc

            if response.is_success:
                return decode_body(response)

            if response.status_code in RETRYABLE_STATUS and attempt < retries:
                await asyncio.sleep(backoff_seconds(attempt, response.headers))
                attempt += 1
                continue

            raise parse_error(
                response.status_code, decode_body(response), response.headers
            )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

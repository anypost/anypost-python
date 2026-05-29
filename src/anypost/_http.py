"""Synchronous HTTP transport: retries, backoff, idempotency, error mapping."""

from __future__ import annotations

import platform
import random
import time
import uuid
from typing import Any, Mapping, Optional, Union

import httpx

from ._exceptions import (
    AnypostError,
    APIConnectionError,
    parse_error,
    retry_after_seconds,
)
from ._version import __version__

RETRYABLE_STATUS = frozenset({429, 502, 503})
_MAX_BACKOFF_SECONDS = 8.0
_BASE_BACKOFF_SECONDS = 0.5

QueryValue = Union[str, int, float, bool, None]


def user_agent() -> str:
    return f"anypost-python/{__version__} Python/{platform.python_version()}"


def clean_query(query: Optional[Mapping[str, QueryValue]]) -> dict[str, str]:
    """Drop ``None`` values and stringify the rest for the query string."""
    if not query:
        return {}
    out: dict[str, str] = {}
    for key, value in query.items():
        if value is None:
            continue
        out[key] = "true" if value is True else "false" if value is False else str(value)
    return out


def build_headers(
    api_key: str,
    default_headers: Mapping[str, str],
    *,
    has_body: bool,
    idempotent: bool,
    idempotency_key: Optional[str],
    max_retries: int,
    extra_headers: Optional[Mapping[str, str]],
) -> dict[str, str]:
    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": user_agent(),
        **dict(default_headers),
    }
    if has_body:
        headers["Content-Type"] = "application/json"
    if idempotent:
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        elif max_retries > 0:
            # Auto-key so built-in retries of a send cannot deliver twice.
            headers["Idempotency-Key"] = str(uuid.uuid4())
    if extra_headers:
        headers.update(extra_headers)
    return headers


def backoff_seconds(attempt: int, headers: Optional[Mapping[str, str]]) -> float:
    if headers is not None:
        after = retry_after_seconds(headers)
        if after is not None:
            return min(after, _MAX_BACKOFF_SECONDS)
    ceiling = min(_BASE_BACKOFF_SECONDS * (2**attempt), _MAX_BACKOFF_SECONDS)
    return random.random() * ceiling  # full jitter


def decode_body(response: httpx.Response) -> Any:
    if response.status_code == 204 or not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return response.text


def connection_message(exc: Exception) -> str:
    if isinstance(exc, httpx.TimeoutException):
        return "Request timed out before a response."
    return f"Could not reach Anypost: {exc}"


class HttpClient:
    """Owns an :class:`httpx.Client` and implements the request loop."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout: float,
        max_retries: int,
        default_headers: Mapping[str, str],
        client: Optional[httpx.Client] = None,
    ) -> None:
        self._api_key = api_key
        self._max_retries = max_retries
        self._default_headers = dict(default_headers)
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=base_url, timeout=timeout
        )

    def request(
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
        params = clean_query(query)
        kwargs: dict[str, Any] = {"headers": headers, "params": params}
        if body is not None:
            kwargs["json"] = body
        if timeout is not None:
            kwargs["timeout"] = timeout

        attempt = 0
        while True:
            try:
                response = self._client.request(method, path, **kwargs)
            except httpx.RequestError as exc:
                if attempt < retries:
                    time.sleep(backoff_seconds(attempt, None))
                    attempt += 1
                    continue
                raise APIConnectionError(connection_message(exc), exc) from exc

            if response.is_success:
                return decode_body(response)

            if response.status_code in RETRYABLE_STATUS and attempt < retries:
                time.sleep(backoff_seconds(attempt, response.headers))
                attempt += 1
                continue

            raise parse_error(
                response.status_code, decode_body(response), response.headers
            )

    def close(self) -> None:
        if self._owns_client:
            self._client.close()


__all__ = ["HttpClient", "AnypostError"]

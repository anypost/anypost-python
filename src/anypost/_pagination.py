"""Cursor pagination for list endpoints."""

from __future__ import annotations

from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Generic,
    Iterator,
    Optional,
    TypeVar,
)

T = TypeVar("T")


class Page(Generic[T]):
    """One page of a list result.

    Mirrors the wire envelope (``data``, ``has_more``, ``next_cursor``) and is
    iterable: iterating walks every remaining page automatically, re-fetching
    with ``after = next_cursor``.

    ::

        page = client.domains.list()       # one page; cursor via page.next_cursor
        for domain in page.data: ...

        for domain in client.domains.list():   # every domain, across all pages
            ...
    """

    def __init__(
        self, response: dict[str, Any], fetch_next: Callable[[str], "Page[T]"]
    ) -> None:
        self.data: list[T] = response.get("data", [])
        self.has_more: bool = response.get("has_more", False)
        self.next_cursor: Optional[str] = response.get("next_cursor")
        self._fetch_next = fetch_next

    def get_next_page(self) -> Optional["Page[T]"]:
        """Fetch the next page, or ``None`` when there are no more."""
        if not self.has_more or self.next_cursor is None:
            return None
        return self._fetch_next(self.next_cursor)

    def __iter__(self) -> Iterator[T]:
        page: Optional[Page[T]] = self
        while page is not None:
            yield from page.data
            page = page.get_next_page()


class AsyncPage(Generic[T]):
    """One page of a list result from an async client.

    Mirrors :class:`Page` but is async-iterable: ``async for`` walks every
    remaining page automatically.

    ::

        page = await client.domains.list()
        for domain in page.data: ...

        async for domain in await client.domains.list():
            ...
    """

    def __init__(
        self,
        response: dict[str, Any],
        fetch_next: Callable[[str], Awaitable["AsyncPage[T]"]],
    ) -> None:
        self.data: list[T] = response.get("data", [])
        self.has_more: bool = response.get("has_more", False)
        self.next_cursor: Optional[str] = response.get("next_cursor")
        self._fetch_next = fetch_next

    async def get_next_page(self) -> Optional["AsyncPage[T]"]:
        """Fetch the next page, or ``None`` when there are no more."""
        if not self.has_more or self.next_cursor is None:
            return None
        return await self._fetch_next(self.next_cursor)

    async def __aiter__(self) -> AsyncIterator[T]:
        page: Optional[AsyncPage[T]] = self
        while page is not None:
            for item in page.data:
                yield item
            page = await page.get_next_page()

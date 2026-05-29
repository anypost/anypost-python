"""Cursor pagination: single page access and auto-iteration across pages."""

from __future__ import annotations

import httpx
from conftest import json_response, make_client


def paged_domains(request: httpx.Request) -> httpx.Response:
    after = request.url.params.get("after")
    if after is None:
        return json_response(
            200,
            {
                "data": [{"id": "domain_1"}, {"id": "domain_2"}],
                "has_more": True,
                "next_cursor": "cursor_2",
            },
        )
    return json_response(
        200,
        {"data": [{"id": "domain_3"}], "has_more": False, "next_cursor": None},
    )


def test_single_page_fields() -> None:
    client, _ = make_client(paged_domains)
    page = client.domains.list()
    assert [d["id"] for d in page.data] == ["domain_1", "domain_2"]
    assert page.has_more is True
    assert page.next_cursor == "cursor_2"


def test_iterates_every_page() -> None:
    client, rec = make_client(paged_domains)
    ids = [d["id"] for d in client.domains.list()]
    assert ids == ["domain_1", "domain_2", "domain_3"]
    assert len(rec.requests) == 2


def test_get_next_page_returns_none_at_end() -> None:
    client, _ = make_client(paged_domains)
    first = client.domains.list()
    second = first.get_next_page()
    assert second is not None
    assert second.get_next_page() is None


def test_list_params_become_query() -> None:
    client, rec = make_client(paged_domains)
    client.domains.list({"limit": 50})
    assert rec.last.url.params["limit"] == "50"


def test_event_tags_joined_comma() -> None:
    client, rec = make_client(
        lambda r: json_response(200, {"data": [], "has_more": False, "next_cursor": None})
    )
    client.events.list({"tags": ["a", "b"], "event_type": "email.bounced"})
    assert rec.last.url.params["tags"] == "a,b"
    assert rec.last.url.params["event_type"] == "email.bounced"

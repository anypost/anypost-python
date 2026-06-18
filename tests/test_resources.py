"""Path, method, and body shape for the management resources."""

from __future__ import annotations

import httpx
from conftest import json_response, make_client


def echo(request: httpx.Request) -> httpx.Response:
    return json_response(200, {"id": "x", "ok": True})


def test_domains_crud_and_verify() -> None:
    client, rec = make_client(echo)

    client.domains.create({"name": "example.com"})
    assert (rec.last.method, rec.last.url.path) == ("POST", "/v1/domains")

    client.domains.get("domain_1")
    assert (rec.last.method, rec.last.url.path) == ("GET", "/v1/domains/domain_1")

    client.domains.update("domain_1", {"tracking": {"opens_enabled": True}})
    assert (rec.last.method, rec.last.url.path) == ("PATCH", "/v1/domains/domain_1")
    assert rec.body()["tracking"]["opens_enabled"] is True

    client.domains.verify("domain_1")
    assert (rec.last.method, rec.last.url.path) == (
        "POST",
        "/v1/domains/domain_1/verify",
    )

    client.domains.delete("domain_1")
    assert (rec.last.method, rec.last.url.path) == ("DELETE", "/v1/domains/domain_1")


def test_events_expose_bot_on_proxied_open() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            200,
            {
                "data": [
                    {
                        "id": "evt_bot",
                        "type": "email.opened",
                        "tracking": {"bot": {"source": "google", "kind": "proxy"}},
                    },
                    {"id": "evt_human", "type": "email.opened", "tracking": None},
                ],
                "has_more": False,
                "next_cursor": None,
            },
        )

    client, _ = make_client(handler)
    page = client.events.list({"event_type": "email.opened"})

    bot = page.data[0]["tracking"]["bot"]
    assert (bot["source"], bot["kind"]) == ("google", "proxy")
    # A human open carries no bot classification.
    assert page.data[1]["tracking"] is None


def test_template_draft_publish_flow() -> None:
    client, rec = make_client(echo)

    client.templates.update_draft("template_1", {"subject": "Hi", "markdown": "# Hi"})
    assert (rec.last.method, rec.last.url.path) == (
        "PATCH",
        "/v1/templates/template_1/draft",
    )
    assert rec.body()["subject"] == "Hi"

    client.templates.publish("template_1")
    assert (rec.last.method, rec.last.url.path) == (
        "POST",
        "/v1/templates/template_1/publish",
    )

    client.templates.duplicate("template_1")
    assert rec.last.url.path == "/v1/templates/template_1/duplicate"
    assert rec.last.content == b""  # no body when params omitted


def test_api_keys_create_and_update() -> None:
    client, rec = make_client(echo)
    client.api_keys.create({"name": "Prod", "permissions": "send_only"})
    assert (rec.last.method, rec.last.url.path) == ("POST", "/v1/api-keys")
    assert rec.body()["permissions"] == "send_only"


def test_webhooks_test_and_rotate() -> None:
    client, rec = make_client(echo)
    client.webhooks.test("wh_1")
    assert rec.last.url.path == "/v1/webhooks/wh_1/test"
    client.webhooks.rotate_secret("wh_1")
    assert rec.last.url.path == "/v1/webhooks/wh_1/rotate-secret"


def test_suppressions_compound_and_email_paths() -> None:
    client, rec = make_client(echo)

    client.suppressions.get("user@example.com", "*")
    # httpx normalizes @ and * (both valid path chars) back to literal form.
    assert rec.last.url.path == "/v1/suppressions/user@example.com/*"

    client, rec = make_client(
        lambda r: json_response(200, {"data": [{"id": "sup_1"}]})
    )
    rows = client.suppressions.list_for_email("user@example.com")
    assert rows == [{"id": "sup_1"}]
    assert rec.last.url.path == "/v1/suppressions/user@example.com"


def test_whoami() -> None:
    body = {
        "team": {"id": "t_1", "name": "Acme"},
        "api_key": {"id": "k", "permissions": "full"},
    }
    client, rec = make_client(lambda r: json_response(200, body))
    me = client.whoami()
    assert me["team"]["name"] == "Acme"
    assert rec.last.url.path == "/v1/whoami"

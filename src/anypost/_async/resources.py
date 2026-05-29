"""Async resource clients. Mirror the sync resources in :mod:`anypost.resources`."""

from __future__ import annotations

from typing import Any, List, Optional
from urllib.parse import quote

from .._async_http import AsyncHttpClient
from .._pagination import AsyncPage
from ..resources.email import _encode_attachments
from ..types.api_key import (
    ApiKey,
    ApiKeyCreateParams,
    ApiKeyUpdateParams,
    ApiKeyWithSecret,
)
from ..types.common import ListParams
from ..types.domain import Domain, DomainCreateParams, DomainUpdateParams
from ..types.email import BatchResponse, EmailBatchParams, EmailSendParams, SendResponse
from ..types.event import Event, EventListParams
from ..types.identity import WhoamiResponse
from ..types.suppression import (
    Suppression,
    SuppressionCreateParams,
    SuppressionListParams,
)
from ..types.template import (
    Template,
    TemplateCreateParams,
    TemplateDraft,
    TemplateDraftParams,
    TemplateDuplicateParams,
    TemplateUpdateParams,
)
from ..types.webhook import (
    Webhook,
    WebhookCreateParams,
    WebhookTestResult,
    WebhookUpdateParams,
    WebhookWithSecret,
)


class AsyncEmail:
    """Operations on the ``/email`` endpoints."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def send(
        self, email: EmailSendParams, *, idempotency_key: Optional[str] = None
    ) -> SendResponse:
        """Send a single message. See :meth:`anypost.resources.email.Email.send`."""
        return await self._http.request(
            "POST",
            "/email",
            body=_encode_attachments(email),
            idempotent=True,
            idempotency_key=idempotency_key,
        )

    async def send_batch(
        self, batch: EmailBatchParams, *, idempotency_key: Optional[str] = None
    ) -> BatchResponse:
        """Send 1-100 messages. A ``207`` returns normally; it does not raise."""
        body: dict[str, Any] = dict(batch)
        if batch.get("defaults"):
            body["defaults"] = _encode_attachments(batch["defaults"])
        body["emails"] = [_encode_attachments(e) for e in batch["emails"]]
        return await self._http.request(
            "POST",
            "/email/batch",
            body=body,
            idempotent=True,
            idempotency_key=idempotency_key,
        )


class AsyncDomains:
    """Operations on the ``/domains`` endpoints."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def list(self, params: Optional[ListParams] = None) -> AsyncPage[Domain]:
        return await self._fetch_page(params)

    async def create(self, params: DomainCreateParams) -> Domain:
        return await self._http.request("POST", "/domains", body=params)

    async def get(self, id: str) -> Domain:
        return await self._http.request("GET", f"/domains/{quote(id, safe='')}")

    async def update(self, id: str, params: DomainUpdateParams) -> Domain:
        return await self._http.request(
            "PATCH", f"/domains/{quote(id, safe='')}", body=params
        )

    async def delete(self, id: str) -> None:
        await self._http.request("DELETE", f"/domains/{quote(id, safe='')}")

    async def verify(self, id: str) -> Domain:
        return await self._http.request("POST", f"/domains/{quote(id, safe='')}/verify")

    async def _fetch_page(self, params: Optional[ListParams]) -> AsyncPage[Domain]:
        params = params or {}
        response = await self._http.request(
            "GET",
            "/domains",
            query={"limit": params.get("limit"), "after": params.get("after")},
        )
        return AsyncPage(
            response, lambda after: self._fetch_page({**params, "after": after})
        )


class AsyncApiKeys:
    """Operations on the ``/api-keys`` endpoints."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def list(self, params: Optional[ListParams] = None) -> AsyncPage[ApiKey]:
        return await self._fetch_page(params)

    async def create(self, params: ApiKeyCreateParams) -> ApiKeyWithSecret:
        return await self._http.request("POST", "/api-keys", body=params)

    async def get(self, id: str) -> ApiKey:
        return await self._http.request("GET", f"/api-keys/{quote(id, safe='')}")

    async def update(self, id: str, params: ApiKeyUpdateParams) -> ApiKey:
        return await self._http.request(
            "PATCH", f"/api-keys/{quote(id, safe='')}", body=params
        )

    async def delete(self, id: str) -> None:
        await self._http.request("DELETE", f"/api-keys/{quote(id, safe='')}")

    async def _fetch_page(self, params: Optional[ListParams]) -> AsyncPage[ApiKey]:
        params = params or {}
        response = await self._http.request(
            "GET",
            "/api-keys",
            query={"limit": params.get("limit"), "after": params.get("after")},
        )
        return AsyncPage(
            response, lambda after: self._fetch_page({**params, "after": after})
        )


class AsyncTemplates:
    """Operations on the ``/templates`` endpoints."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def list(self, params: Optional[ListParams] = None) -> AsyncPage[Template]:
        return await self._fetch_page(params)

    async def create(self, params: TemplateCreateParams) -> Template:
        return await self._http.request("POST", "/templates", body=params)

    async def get(self, id: str) -> Template:
        return await self._http.request("GET", f"/templates/{quote(id, safe='')}")

    async def update(self, id: str, params: TemplateUpdateParams) -> Template:
        return await self._http.request(
            "PATCH", f"/templates/{quote(id, safe='')}", body=params
        )

    async def delete(self, id: str) -> None:
        await self._http.request("DELETE", f"/templates/{quote(id, safe='')}")

    async def duplicate(
        self, id: str, params: Optional[TemplateDuplicateParams] = None
    ) -> Template:
        return await self._http.request(
            "POST", f"/templates/{quote(id, safe='')}/duplicate", body=params or None
        )

    async def get_draft(self, id: str) -> TemplateDraft:
        return await self._http.request("GET", f"/templates/{quote(id, safe='')}/draft")

    async def update_draft(self, id: str, params: TemplateDraftParams) -> TemplateDraft:
        return await self._http.request(
            "PATCH", f"/templates/{quote(id, safe='')}/draft", body=params
        )

    async def delete_draft(self, id: str) -> None:
        await self._http.request("DELETE", f"/templates/{quote(id, safe='')}/draft")

    async def publish(self, id: str) -> Template:
        return await self._http.request("POST", f"/templates/{quote(id, safe='')}/publish")

    async def _fetch_page(self, params: Optional[ListParams]) -> AsyncPage[Template]:
        params = params or {}
        response = await self._http.request(
            "GET",
            "/templates",
            query={"limit": params.get("limit"), "after": params.get("after")},
        )
        return AsyncPage(
            response, lambda after: self._fetch_page({**params, "after": after})
        )


class AsyncSuppressions:
    """Operations on the ``/suppressions`` endpoints."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def list(
        self, params: Optional[SuppressionListParams] = None
    ) -> AsyncPage[Suppression]:
        return await self._fetch_page(params)

    async def create(self, params: SuppressionCreateParams) -> Suppression:
        return await self._http.request("POST", "/suppressions", body=params)

    async def get(self, email: str, topic: str) -> Suppression:
        return await self._http.request(
            "GET", f"/suppressions/{quote(email, safe='')}/{quote(topic, safe='')}"
        )

    async def delete(self, email: str, topic: str) -> None:
        await self._http.request(
            "DELETE", f"/suppressions/{quote(email, safe='')}/{quote(topic, safe='')}"
        )

    async def list_for_email(self, email: str) -> List[Suppression]:
        response = await self._http.request("GET", f"/suppressions/{quote(email, safe='')}")
        return response["data"]

    async def delete_for_email(self, email: str) -> None:
        await self._http.request("DELETE", f"/suppressions/{quote(email, safe='')}")

    async def _fetch_page(
        self, params: Optional[SuppressionListParams]
    ) -> AsyncPage[Suppression]:
        params = params or {}
        response = await self._http.request(
            "GET",
            "/suppressions",
            query={
                "limit": params.get("limit"),
                "after": params.get("after"),
                "email_contains": params.get("email_contains"),
                "topic": params.get("topic"),
                "reason": params.get("reason"),
                "origin": params.get("origin"),
            },
        )
        return AsyncPage(
            response, lambda after: self._fetch_page({**params, "after": after})
        )


class AsyncWebhooks:
    """Operations on the ``/webhooks`` endpoints."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def list(self, params: Optional[ListParams] = None) -> AsyncPage[Webhook]:
        return await self._fetch_page(params)

    async def create(self, params: WebhookCreateParams) -> WebhookWithSecret:
        return await self._http.request("POST", "/webhooks", body=params)

    async def get(self, id: str) -> Webhook:
        return await self._http.request("GET", f"/webhooks/{quote(id, safe='')}")

    async def update(self, id: str, params: WebhookUpdateParams) -> Webhook:
        return await self._http.request(
            "PATCH", f"/webhooks/{quote(id, safe='')}", body=params
        )

    async def delete(self, id: str) -> None:
        await self._http.request("DELETE", f"/webhooks/{quote(id, safe='')}")

    async def test(self, id: str) -> WebhookTestResult:
        return await self._http.request("POST", f"/webhooks/{quote(id, safe='')}/test")

    async def rotate_secret(self, id: str) -> WebhookWithSecret:
        return await self._http.request(
            "POST", f"/webhooks/{quote(id, safe='')}/rotate-secret"
        )

    async def _fetch_page(self, params: Optional[ListParams]) -> AsyncPage[Webhook]:
        params = params or {}
        response = await self._http.request(
            "GET",
            "/webhooks",
            query={"limit": params.get("limit"), "after": params.get("after")},
        )
        return AsyncPage(
            response, lambda after: self._fetch_page({**params, "after": after})
        )


class AsyncEvents:
    """Read access to the ``/events`` stream."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def list(self, params: Optional[EventListParams] = None) -> AsyncPage[Event]:
        return await self._fetch_page(params)

    async def _fetch_page(self, params: Optional[EventListParams]) -> AsyncPage[Event]:
        params = params or {}
        tags = params.get("tags")
        response = await self._http.request(
            "GET",
            "/events",
            query={
                "limit": params.get("limit"),
                "after": params.get("after"),
                "start": params.get("start"),
                "end": params.get("end"),
                "event_type": params.get("event_type"),
                "recipient": params.get("recipient"),
                "email_id": params.get("email_id"),
                "message_id": params.get("message_id"),
                "domain": params.get("domain"),
                "topic": params.get("topic"),
                "campaign": params.get("campaign"),
                "template_id": params.get("template_id"),
                "tags": ",".join(tags) if tags else None,
            },
        )
        return AsyncPage(
            response, lambda after: self._fetch_page({**params, "after": after})
        )


class AsyncIdentity:
    """Identity operations."""

    def __init__(self, http: AsyncHttpClient) -> None:
        self._http = http

    async def whoami(self) -> WhoamiResponse:
        return await self._http.request("GET", "/whoami")

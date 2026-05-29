"""The ``/templates`` resource, including the draft/publish flow."""

from __future__ import annotations

from typing import Optional
from urllib.parse import quote

from .._http import HttpClient
from .._pagination import Page
from ..types.common import ListParams
from ..types.template import (
    Template,
    TemplateCreateParams,
    TemplateDraft,
    TemplateDraftParams,
    TemplateDuplicateParams,
    TemplateUpdateParams,
)


class Templates:
    """Operations on the ``/templates`` endpoints, including the draft/publish flow."""

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self, params: Optional[ListParams] = None) -> Page[Template]:
        """List the team's templates, newest-first."""
        return self._fetch_page(params)

    def create(self, params: TemplateCreateParams) -> Template:
        """Create a template. It starts unpublished — publish it before sending."""
        return self._http.request("POST", "/templates", body=params)

    def get(self, id: str) -> Template:
        """Retrieve a template, including its published content."""
        return self._http.request("GET", f"/templates/{quote(id, safe='')}")

    def update(self, id: str, params: TemplateUpdateParams) -> Template:
        """Update a template's ``name``. Body content lives on the draft."""
        return self._http.request("PATCH", f"/templates/{quote(id, safe='')}", body=params)

    def delete(self, id: str) -> None:
        """Permanently delete a template."""
        self._http.request("DELETE", f"/templates/{quote(id, safe='')}")

    def duplicate(
        self, id: str, params: Optional[TemplateDuplicateParams] = None
    ) -> Template:
        """Copy a template.

        The copy starts unpublished with a draft seeded from the source's
        current editable content, and must be published before sending.
        """
        return self._http.request(
            "POST", f"/templates/{quote(id, safe='')}/duplicate", body=params or None
        )

    def get_draft(self, id: str) -> TemplateDraft:
        """Retrieve the template's unpublished draft. Raises ``not_found`` if none exists."""
        return self._http.request("GET", f"/templates/{quote(id, safe='')}/draft")

    def update_draft(self, id: str, params: TemplateDraftParams) -> TemplateDraft:
        """Create or update the template's draft. Idempotent upsert; published content untouched."""
        return self._http.request(
            "PATCH", f"/templates/{quote(id, safe='')}/draft", body=params
        )

    def delete_draft(self, id: str) -> None:
        """Discard the template's draft without touching published content."""
        self._http.request("DELETE", f"/templates/{quote(id, safe='')}/draft")

    def publish(self, id: str) -> Template:
        """Promote the draft into the published slot, consuming the draft."""
        return self._http.request("POST", f"/templates/{quote(id, safe='')}/publish")

    def _fetch_page(self, params: Optional[ListParams]) -> Page[Template]:
        params = params or {}
        response = self._http.request(
            "GET",
            "/templates",
            query={"limit": params.get("limit"), "after": params.get("after")},
        )
        return Page(
            response, lambda after: self._fetch_page({**params, "after": after})
        )

"""Types for the ``/templates`` endpoints."""

from __future__ import annotations

from typing import Optional

from typing_extensions import Literal, NotRequired, TypedDict

#: Authoring format. Immutable once a template exists.
TemplateKind = Literal["html", "markdown"]


class Template(TypedDict):
    """A reusable email template.

    The ``subject``/``html``/``text``/``markdown`` fields hold the *published*
    content and are ``None`` until the template is first published. Edits land
    in a draft; ``templates.publish`` promotes the draft into the published
    slot. Sends always use the published content.
    """

    #: ``template_``-prefixed id.
    id: str
    #: Identifier for the template, unique within the team.
    name: str
    #: Published subject line. ``None`` until first published.
    subject: Optional[str]
    kind: TemplateKind
    #: Published HTML body. ``None`` until first published.
    html: Optional[str]
    #: Published plain-text body, always machine-derived. ``None`` until first published.
    text: Optional[str]
    #: Published emailmd source. Only set for ``kind=markdown``, else ``None``.
    markdown: Optional[str]
    #: Whether an unpublished draft is pending.
    has_draft: bool
    #: When last published, or ``None`` if never.
    published_at: Optional[str]
    created_at: str
    updated_at: str


class TemplateDraft(TypedDict):
    """The unpublished draft content for a template."""

    subject: Optional[str]
    html: Optional[str]
    #: Always machine-derived from the draft's ``html``/``markdown``.
    text: Optional[str]
    markdown: Optional[str]
    updated_at: str


class TemplateCreateParams(TypedDict):
    """Body for ``templates.create``.

    The new template starts unpublished. For ``kind=html`` supply ``html``;
    for ``kind=markdown`` supply ``markdown``. The plain-text body is always
    derived server-side.
    """

    name: str
    subject: NotRequired[Optional[str]]
    #: Defaults to ``html``. Immutable once the template exists.
    kind: NotRequired[TemplateKind]
    html: NotRequired[Optional[str]]
    markdown: NotRequired[Optional[str]]


class TemplateUpdateParams(TypedDict):
    """Body for ``templates.update``. Only ``name`` is mutable; content is draft-versioned."""

    name: str


class TemplateDraftParams(TypedDict, total=False):
    """Body for ``templates.update_draft``. Idempotent upsert of the draft."""

    subject: Optional[str]
    html: Optional[str]
    markdown: Optional[str]


class TemplateDuplicateParams(TypedDict, total=False):
    """Body for ``templates.duplicate``."""

    #: Name for the copy. Defaults to ``"<source name> (copy)"`` when omitted.
    name: str

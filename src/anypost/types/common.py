"""Shared types used across multiple resources."""

from __future__ import annotations

from typing import Dict, Union

from typing_extensions import Literal, NotRequired, TypedDict

#: Permission level of an API key.
Permissions = Literal["full", "send_only"]

#: Custom message headers as a name -> value map. Platform-controlled and
#: trust-signal headers are dropped server-side; at most 25 entries survive.
HeaderMap = Dict[str, str]


class Attachment(TypedDict):
    """An inline attachment."""

    filename: str
    #: File contents. Pass raw ``bytes`` and the client base64-encodes them;
    #: pass an already base64-encoded ``str`` and it is sent as-is.
    content: Union[bytes, str]
    #: MIME type. Defaults to ``application/octet-stream`` server-side.
    content_type: NotRequired[str]
    #: Content-ID for an inline attachment referenced from the HTML via ``cid:``.
    content_id: NotRequired[str]


class Tracking(TypedDict, total=False):
    """Per-message override of the sending domain's open/click tracking defaults."""

    #: Inject the open-tracking pixel into the HTML body.
    opens: bool
    #: Rewrite links for click tracking.
    clicks: bool


class Unsubscribe(TypedDict):
    """One-click unsubscribe behavior."""

    #: ``generate`` mints a per-recipient signed token and injects RFC 8058
    #: unsubscribe headers (requires ``topic``). ``none`` injects nothing.
    mode: Literal["generate", "none"]
    #: Human-readable label rendered on the hosted confirmation page.
    display_name: NotRequired[str]


class ListParams(TypedDict, total=False):
    """Shared query parameters for every list endpoint."""

    #: Items per page, 1-100. Defaults to 20 server-side.
    limit: int
    #: A cursor from a previous page's ``next_cursor``. Opaque — do not parse.
    after: str

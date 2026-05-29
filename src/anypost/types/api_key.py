"""Types for the ``/api-keys`` endpoints."""

from __future__ import annotations

from typing import List, Optional

from typing_extensions import NotRequired, TypedDict

from .common import Permissions


class ApiKey(TypedDict):
    """An API key's metadata. The plaintext secret is never returned here."""

    #: ``key_``-prefixed id.
    id: str
    name: str
    #: The first 12 characters of the key, shown for identification.
    key_prefix: str
    permissions: Permissions
    #: Domains this key may send from. ``None`` means all verified domains.
    allowed_domains: Optional[List[str]]
    #: IPs or CIDR blocks allowed to use this key. ``None`` means all IPs.
    allowed_ips: Optional[List[str]]
    #: When the key was last used, or ``None`` if never.
    last_used_at: Optional[str]
    created_at: str


class ApiKeyWithSecret(ApiKey):
    """A newly created API key, including its plaintext secret."""

    #: The full API key. Returned only once, at creation. Store it securely.
    key: str


class ApiKeyCreateParams(TypedDict):
    """Body for ``api_keys.create``."""

    name: str
    permissions: Permissions
    #: Restrict sending to these domains. Omit or ``None`` for all verified domains.
    allowed_domains: NotRequired[Optional[List[str]]]
    #: Restrict use to these IPs/CIDRs. Omit or ``None`` for all IPs.
    allowed_ips: NotRequired[Optional[List[str]]]


class ApiKeyUpdateParams(TypedDict):
    """Body for ``api_keys.update``. The plaintext secret is not rotated here."""

    name: str
    permissions: Permissions
    #: Pass an empty list or ``None`` to lift the domain restriction.
    allowed_domains: NotRequired[Optional[List[str]]]
    #: Pass an empty list or ``None`` to lift the IP restriction.
    allowed_ips: NotRequired[Optional[List[str]]]

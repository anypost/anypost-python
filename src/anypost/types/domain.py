"""Types for the ``/domains`` endpoints."""

from __future__ import annotations

from typing import List, Optional

from typing_extensions import Literal, TypedDict


class DnsRecord(TypedDict):
    """A DNS record to publish to verify a domain or its tracking."""

    #: Record type. ``CNAME`` is the only value today.
    type: Literal["CNAME"]
    #: Record name relative to the registered (ICANN) apex of the sending
    #: domain — the form most provider UIs accept.
    name: str
    #: The CNAME target (absolute FQDN).
    value: str
    #: What the record is for.
    purpose: Literal["verification", "dkim", "tracking"]


class VerificationFailure(TypedDict):
    """A stable failure category plus a human-readable message."""

    #: Stable, switchable failure code. The set varies by field.
    code: str
    #: Human-readable message with the domain's record names interpolated.
    message: str


class DomainTracking(TypedDict):
    """Branded open/click tracking for a domain. Independent of mail-flow verification."""

    opens_enabled: bool
    clicks_enabled: bool
    #: Tracking subdomain prefix, or ``None`` when tracking is off.
    subdomain: Optional[str]
    #: Branded-tracking DNS records to publish. Empty when tracking is off.
    dns_records: List[DnsRecord]
    #: ``disabled`` when no flag is on, ``pending`` until the CNAME resolves, then ``verified``.
    status: Literal["disabled", "pending", "verified"]
    #: Most recent tracking-CNAME failure, or ``None``.
    verification_failure: Optional[VerificationFailure]
    #: When the tracking CNAME was last observed resolving, or ``None``.
    verified_at: Optional[str]


class Domain(TypedDict):
    """A sending domain and its mail-flow verification state."""

    #: ``domain_``-prefixed id.
    id: str
    #: The domain name, e.g. ``example.com``.
    name: str
    #: ``pending`` until the mail-flow CNAMEs resolve, then ``verified``.
    status: Literal["pending", "verified"]
    #: Mail-flow DNS records: one verification CNAME plus one per DKIM selector.
    dns_records: List[DnsRecord]
    #: Most recent mail-flow verification failure, or ``None``.
    verification_failure: Optional[VerificationFailure]
    #: Branded tracking configuration and its independent status.
    tracking: DomainTracking
    created_at: str
    #: When the domain most recently transitioned to ``verified``, or ``None``.
    verified_at: Optional[str]


class DomainCreateParams(TypedDict):
    """Body for ``domains.create``."""

    #: The domain name to add, e.g. ``example.com``.
    name: str


class DomainTrackingParams(TypedDict, total=False):
    opens_enabled: bool
    clicks_enabled: bool
    #: Required when either flag is true; pass ``None`` to clear when both are false.
    subdomain: Optional[str]


class DomainUpdateParams(TypedDict):
    """Body for ``domains.update``. Only tracking is mutable; ``name`` is immutable."""

    tracking: DomainTrackingParams

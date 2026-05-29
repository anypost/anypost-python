"""Base64 encoding for attachment content."""

from __future__ import annotations

import base64


def bytes_to_base64(data: bytes) -> str:
    """Base64-encode raw bytes into an ASCII string."""
    return base64.b64encode(data).decode("ascii")

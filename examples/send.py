"""Send one email.

Run with a real key against the dev gateway:

    ANYPOST_API_KEY=ap_... ANYPOST_BASE_URL=https://<host>/v1 python examples/send.py
"""

from __future__ import annotations

import os

from anypost import Anypost

client = Anypost(base_url=os.environ.get("ANYPOST_BASE_URL", "https://api.anypost.com/v1"))

result = client.email.send(
    {
        "from": "you@yourdomain.com",
        "to": ["someone@example.com"],
        "subject": "Hello from Anypost",
        "text": "It worked.",
    }
)

print("queued:", result["id"], result["created_at"])

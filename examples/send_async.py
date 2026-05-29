"""Send one email with the async client.

    ANYPOST_API_KEY=ap_... ANYPOST_BASE_URL=https://<host>/v1 python examples/send_async.py
"""

from __future__ import annotations

import asyncio
import os

from anypost import AsyncAnypost


async def main() -> None:
    base_url = os.environ.get("ANYPOST_BASE_URL", "https://api.anypost.com/v1")
    async with AsyncAnypost(base_url=base_url) as client:
        result = await client.email.send(
            {
                "from": "you@yourdomain.com",
                "to": ["someone@example.com"],
                "subject": "Hello from Anypost",
                "text": "It worked.",
            }
        )
        print("queued:", result["id"], result["created_at"])


if __name__ == "__main__":
    asyncio.run(main())

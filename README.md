# Anypost Python SDK

The official Python client for the [Anypost](https://anypost.com) email API.

Requires Python 3.9+. Built on [httpx](https://www.python-httpx.org/), with sync and async clients.

This README covers the SDK itself: installation, idioms, and configuration. For platform concepts and the full field-level API reference, see the [Anypost documentation](https://anypost.com/docs).

## Install

```bash
pip install anypost
```

## Quickstart

```python
from anypost import Anypost

client = Anypost("ap_your_api_key")

result = client.email.send({
    "from": "YourCo <you@yourdomain.com>",
    "to": ["you@example.com"],
    "subject": "Welcome to Anypost",
    "html": "<p>Hello, inbox!</p>",
})
print(result["id"])
```

The constructor also reads `ANYPOST_API_KEY` from the environment:

```python
client = Anypost()
```

Keep the key server-side. It is a bearer credential; never ship it to a browser or mobile app.

Request bodies are plain dicts that match the API one-to-one, including the `"from"` key, which a dict literal accepts even though `from` is a reserved word. Responses are dicts too, typed with `TypedDict` for editor autocomplete.

## Async

Every operation has an async twin on `AsyncAnypost`. Same methods, same shapes: `await` them, and iterate pages with `async for`.

```python
import asyncio
from anypost import AsyncAnypost

async def main():
    async with AsyncAnypost("ap_your_api_key") as client:
        result = await client.email.send({
            "from": "YourCo <you@yourdomain.com>",
            "to": ["you@example.com"],
            "subject": "Welcome to Anypost",
            "html": "<p>Hello, inbox!</p>",
        })
        print(result["id"])

asyncio.run(main())
```

The rest of this README shows the sync client. The async client is identical with `await`.

## Sending

One of `text`, `html`, or `template_id` is required. All recipients in `to`, `cc`, and `bcc` share one envelope and count against a combined limit of 50.

```python
client.email.send({
    "from": "YourCo <you@yourdomain.com>",
    "to": ["a@example.com", "b@example.com"],
    "cc": ["team@example.com"],
    "reply_to": "support@yourdomain.com",
    "subject": "Receipt #4823",
    "html": "<p>Thanks for your order.</p>",
    "text": "Thanks for your order.",
    "tags": ["receipt"],
})
```

Pass attachment `content` as raw `bytes` and the client base64-encodes it; pass an already-encoded `str` and it is sent as-is. The request body is capped at 5 MB.

```python
from pathlib import Path

client.email.send({
    "from": "YourCo <you@yourdomain.com>",
    "to": ["someone@example.com"],
    "subject": "Your report",
    "text": "Attached.",
    "attachments": [
        {"filename": "report.pdf", "content": Path("report.pdf").read_bytes()},
    ],
})
```

Send with a published template and per-recipient variables:

```python
client.email.send({
    "from": "YourCo <you@yourdomain.com>",
    "to": ["someone@example.com"],
    "template_id": "template_018f2c5e-3a40-7a91-9c25-3a0b1d5e6f78",
    "variables": {"name": "Ada", "plan": "pro"},
})
```

See the [send reference](https://anypost.com/docs/reference/emails) for the complete field list.

## Batch

Send 1 to 100 independent messages in one request. `defaults` fills any field an entry omits.

```python
result = client.email.send_batch({
    "defaults": {"from": "YourCo <you@yourdomain.com>"},
    "emails": [
        {"to": ["a@example.com"], "subject": "Hi A", "text": "..."},
        {"to": ["b@example.com"], "subject": "Hi B", "text": "..."},
    ],
})
```

A batch with mixed outcomes returns HTTP `207` and resolves normally. Inspect each entry rather than relying on a raised error:

```python
print(result["summary"])  # {"total": ..., "queued": ..., "failed": ...}

for entry in result["data"]:
    if entry["status"] == "queued":
        print(entry["index"], entry["id"])
    else:
        print(entry["index"], entry["error"]["type"], entry["error"]["message"])
```

## Domains

Manage sending domains under `client.domains`. Add a domain, publish the DNS records it returns, then verify.

```python
domain = client.domains.create({"name": "example.com"})

for record in domain["dns_records"]:
    print(record["type"], record["name"], "->", record["value"])

checked = client.domains.verify(domain["id"])
if checked["status"] != "verified":
    # verify returns the current domain even while pending; it never raises
    print(checked["verification_failure"])
```

`get`, `update` (tracking config only), and `delete` round out the resource. See [Domains](https://anypost.com/docs/reference/domains) for the verification lifecycle and field reference.

## API keys

Manage keys under `client.api_keys`. The plaintext secret comes back only once, on `create`, as `key`:

```python
created = client.api_keys.create({
    "name": "Production server",
    "permissions": "send_only",
    "allowed_domains": ["example.com"],
})
print(created["key"])  # store now; never retrievable again
```

`get` returns metadata only (`key_prefix`, never the secret); `update` and `delete` round out the resource. See [API keys](https://anypost.com/docs/reference/api-keys) for the permission model and cache propagation.

## Templates

Templates use a draft/published model: edits land in a draft, and `publish` promotes it. A template can't be used for sending until it's published.

```python
template = client.templates.create({
    "name": "Welcome email",
    "kind": "html",
    "html": "<h1>Welcome, {{ name }}</h1>",
})

client.templates.publish(template["id"])
```

`kind` (`html` or `markdown`) is immutable once set; the plain-text body is always derived server-side. `get_draft`, `update_draft`, `delete_draft`, `duplicate`, `get`, `update` (name only), and `delete` round out the resource. Send a published template with `template_id` (see [Sending](#sending)). See [Templates](https://anypost.com/docs/reference/templates) for the full model.

## Suppressions

A suppression blocks sends to an address, scoped to a `topic`. The wildcard `*` blocks every topic; a named topic (e.g. `marketing`) leaves transactional traffic untouched.

```python
client.suppressions.create({
    "email": "alice@example.com",
    "topic": "marketing",
    "note": "Customer requested removal",
})

client.suppressions.delete("alice@example.com", "marketing")
```

`get`, `list` (with `email_contains`, `topic`, `reason`, and `origin` filters), `list_for_email`, and `delete_for_email` round out the resource. See [Suppressions](https://anypost.com/docs/reference/suppressions) for scoping and the automatic-suppression rules for bounces and complaints.

## Webhooks

Manage webhook subscriptions under `client.webhooks`. The `signing_secret` comes back only once, on `create`; later reads return only `signing_secret_prefix`.

```python
webhook = client.webhooks.create({
    "name": "Production events",
    "url": "https://hooks.example.com/anypost",
    "events": ["email.delivered", "email.bounced", "email.complained"],
})
print(webhook["signing_secret"])  # store now; never retrievable again
```

`update`, `test`, `rotate_secret`, `get`, `list`, and `delete` round out the resource. See [Webhooks](https://anypost.com/docs/reference/webhooks) for the event catalog, status transitions, and the secret-rotation grace window.

### Verifying deliveries

`verify_webhook_signature` is a standalone function. It needs the signing secret, not an API key, so call it in your handler without a client. Pass the **raw** request body (the exact bytes, before JSON parsing), the `Anypost-Signature` header, and the secret. It returns on success and raises `WebhookVerificationError` otherwise. `unwrap_webhook_event` does the same and returns the parsed delivery.

```python
from anypost import unwrap_webhook_event, WebhookVerificationError

try:
    delivery = unwrap_webhook_event(raw_body, signature_header, secret)
    for event in delivery["events"]:
        print(event["type"], event["data"]["email_id"])
except WebhookVerificationError as err:
    # err.reason: "no_match" | "timestamp_out_of_tolerance" | ...
    return Response(status_code=400)
```

Reach for `verify_webhook_signature` when something else has already parsed the body. Keep the raw bytes for the verify step, then use your framework's parsed object once it passes:

```python
from anypost import verify_webhook_signature, WebhookVerificationError

@app.post("/anypost")
async def anypost_webhook(request):
    raw = await request.body()
    try:
        verify_webhook_signature(raw, request.headers["anypost-signature"], secret)
    except WebhookVerificationError:
        return Response(status_code=400)
    for event in (await request.json())["events"]:
        handle(event)
    return Response(status_code=204)
```

Deliveries older than five minutes are rejected by default to bound replay; pass `tolerance_seconds` to widen, narrow, or disable (`0`) that check. During a secret rotation the header carries a `v1=` component per active secret, and a match on any one passes, so deliveries keep verifying while you redeploy.

## Events

`client.events.list` pages the team's event stream, newest-first. The window defaults to the last 24 hours and is clamped to your plan's retention. Events are read-only and not addressable by id, so there is no `get`.

```python
for event in client.events.list({"event_type": "email.bounced"}):
    print(event["occurred_at"], event["recipient"], event["bounce_classification"])
```

Filter by `start`, `end`, `event_type`, `recipient`, `email_id`, `message_id`, `domain`, `topic`, `campaign`, `template_id`, and `tags`, a list that matches an event carrying *any* of the given tags. Every other filter is exact-match. This is also how you backfill the gap after a webhook endpoint was disabled: page the events that occurred during the outage once it's healthy. See [Events](https://anypost.com/docs/reference/events) for the field reference.

## Pagination

List endpoints return a `Page`. Read one page directly, or iterate it to walk every page; the client fetches each one as needed.

```python
page = client.domains.list({"limit": 50})
page.data         # this page's items
page.has_more     # whether another page exists
page.next_cursor  # pass as "after" to fetch it yourself

for domain in client.domains.list():
    print(domain["name"])  # every domain, across all pages
```

On the async client, `await` the call and iterate with `async for`:

```python
async for domain in await client.domains.list():
    print(domain["name"])
```

## Errors

A failed request raises an `AnypostError` subclass. Branch on `err.type`, the stable machine-readable code, not on the HTTP status.

```python
from anypost import AnypostError, ValidationError, RateLimitError

try:
    client.email.send({"from": from_, "to": to, "subject": subject, "html": html})
except ValidationError as err:
    print(err.errors)  # {"from": ["The from field is required."]}
except RateLimitError as err:
    print(err.retry_after)  # seconds, or None
except AnypostError as err:
    print(err.type, err.status, err.message)
```

| Class | `type` | Status |
|---|---|---|
| `ValidationError` | `validation_error` | `400`, `422` |
| `AuthenticationError` | `authentication_error` | `401` |
| `PermissionError` | `permission_error` | `403` |
| `NotFoundError` | `not_found` | `404` |
| `ConflictError` | `conflict`, `idempotency_concurrent`, `webhook_rotation_in_progress` | `409` |
| `IdempotencyMismatchError` | `idempotency_mismatch` | `422` |
| `RateLimitError` | `rate_limit_exceeded` | `429` |
| `PayloadTooLargeError` | `payload_too_large` | `413` |
| `APIError` | `internal_error`, `provisioning_error` | `5xx` |
| `APIConnectionError` | `connection_error` | none |

Every error carries `type`, `status`, `message`, `request_id`, and the parsed `raw` body.

## Retries and idempotency

The client retries `429`, `502`, `503`, and network failures up to `max_retries` times (default 2), with exponential backoff and full jitter. It honors `Retry-After`.

Sends are made safe to retry automatically: when retries are enabled and you do not pass an `idempotency_key`, the client generates one and reuses it across attempts, so a retried send cannot deliver twice. Pass your own key to dedupe across process restarts:

```python
client.email.send(message, idempotency_key=order_id)
```

## Configuration

```python
Anypost(api_key="ap_your_api_key", base_url=..., timeout=..., max_retries=...)
```

| Option | Default | Description |
|---|---|---|
| `api_key` | `ANYPOST_API_KEY` | Bearer credential (`ap_...`). |
| `base_url` | `https://api.anypost.com/v1` | API base URL. |
| `timeout` | `30.0` | Per-request timeout, in seconds. |
| `max_retries` | `2` | Automatic retries for transient failures. |
| `default_headers` | `{}` | Extra headers sent on every request. |
| `http_client` | a new one | Bring your own `httpx.Client` / `httpx.AsyncClient`. |

`AsyncAnypost` takes the same arguments. `send` and `send_batch` accept a per-call `idempotency_key`.

Close the client when you're done, or use it as a context manager:

```python
with Anypost() as client:
    client.email.send(message)

# async
async with AsyncAnypost() as client:
    await client.email.send(message)
```

## License

MIT

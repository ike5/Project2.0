# Lab 08 — Incoming & Outgoing Webhooks

**You'll:** create an incoming webhook and post to it, register an outgoing webhook
pointed at a tiny local receiver, watch a **signed** delivery arrive, verify its
signature, and observe retries when the receiver is down.

⏱️ ~50 min. Web server + a Celery worker running. Redis + the dev services up.

---

## Part A — Create an incoming webhook

As a workspace **admin** (ann), create one for `#general`:
```bash
curl -s -H "Authorization: Bearer $ACCESS" -H 'content-type: application/json' \
  -X POST localhost:8000/api/webhooks/incoming/ \
  -d "{\"channel\":$CH,\"label\":\"deploys\"}" | jq
```
✅ Expected: a `token` and a `url` like `/api/webhooks/in/<token>/`.

Now post to it **with no auth** (as an external tool would):
```bash
TOKEN=$(curl -s -H "Authorization: Bearer $ACCESS" localhost:8000/api/webhooks/incoming/ | jq -r '.results[0].token // .[0].token')
curl -s -X POST "localhost:8000/api/webhooks/in/$TOKEN/" \
  -H 'content-type: application/json' -d '{"text":"🚀 deploy finished"}' | jq
```
✅ Expected: `{"ok":true,"message_id":...}`. The message appears in `#general` (check
via REST or a connected `wscat`). Bad token → `404`; empty text → `400`.

---

## Part B — A tiny receiver that checks the signature

Save this as `receiver.py` and run it (`python receiver.py`) — it prints whether the
HMAC signature is valid:

```python
import hashlib, hmac
from http.server import BaseHTTPRequestHandler, HTTPServer

SECRET = b"shhh-secret"

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers["Content-Length"]))
        sig = self.headers.get("X-Slackclone-Signature", "")
        expected = "sha256=" + hmac.new(SECRET, body, hashlib.sha256).hexdigest()
        ok = hmac.compare_digest(expected, sig)
        print("signature valid:", ok, "| body:", body.decode())
        self.send_response(200 if ok else 401); self.end_headers()

HTTPServer(("127.0.0.1", 9999), H).serve_forever()
```

---

## Part C — Register it as an outgoing webhook

```bash
curl -s -H "Authorization: Bearer $ACCESS" -H 'content-type: application/json' \
  -X POST localhost:8000/api/webhooks/outgoing/ \
  -d "{\"workspace\":$WS,\"target_url\":\"http://127.0.0.1:9999/\",\"secret\":\"shhh-secret\",\"event\":\"message.created\"}" | jq
```
✅ Expected: `201`. (The `secret` is write-only — you won't see it in GET responses.)

---

## Part D — Trigger a signed delivery

Post any message to a channel in that workspace:
```bash
curl -s -H "Authorization: Bearer $ACCESS" -H 'content-type: application/json' \
  -X POST localhost:8000/api/messages/ -d "{\"channel\":$CH,\"body\":\"hello integrations\"}" >/dev/null
```
✅ In the **receiver** terminal: `signature valid: True | body: {"event":"message.created",...}`.
✅ In the **worker** terminal: the `deliver` task ran and recorded a `WebhookDelivery`.

Confirm the audit record:
```bash
python manage.py shell -c "from webhooks.models import WebhookDelivery as D; print(list(D.objects.values('status_code','attempt','succeeded')))"
```

---

## Part E — Retries when the receiver is down

Stop `receiver.py` (Ctrl+C). Post another message. Watch the worker:
✅ Expected: `deliver` fails, retries with backoff (10s, 20s, …), recording a failed
`WebhookDelivery` each attempt, then gives up after 5. Restart the receiver and post
again — it succeeds on the first try.

---

## What you learned
- Incoming webhooks use a secret URL token (no login) to post into a channel.
- Outgoing webhooks POST signed payloads; receivers verify the HMAC in constant time.
- A `post_save` signal fires delivery for every message, however it was created.
- Celery makes delivery reliable with retries and an auditable record.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 09](../09-nextjs-foundations/).

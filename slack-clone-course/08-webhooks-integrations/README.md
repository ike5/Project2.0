# Module 08 — Webhooks & Integrations

**Goal:** let external tools post into channels (incoming webhooks) and let the app
notify external services about events (outgoing webhooks), all authenticated with
HMAC signatures and delivered reliably via Celery.

⏱️ ~2.5 hours · 🎯 Prereq: Module 07 (Celery working).

> This is how real Slack connects to GitHub, CI, PagerDuty, and a thousand other
> tools. Webhooks are the universal glue of SaaS — and a great lesson in signing,
> verifying, and reliably delivering HTTP.

---

## 1. Two directions

```
 Incoming:  GitHub ──POST──► /api/webhooks/in/<token>/ ──► message in #deploys
 Outgoing:  new message ──POST(signed)──► https://their-service/hook
```

- **Incoming** — *they* call *us*. A secret **token in the URL** is the credential
  (no login). Posting to it drops a message into one channel.
- **Outgoing** — *we* call *them*. We POST events (e.g. `message.created`) to a URL
  they registered, **signed** so they can trust it.

## 2. Incoming webhooks

`IncomingWebhookView` is deliberately auth-free (`authentication_classes = []`): the
unguessable token *is* the secret, so the URL must be treated like a password. It
looks up the active webhook, creates a message authored by the webhook's creator, and
runs the **same** post-create effects as any message — set the channel head,
broadcast over the channel layer, and fan out notifications. So a webhook message is
indistinguishable from a normal one downstream.

## 3. Outgoing webhooks + HMAC signing

When *anything* creates a message, subscribers must be told. We POST a JSON payload
and include a signature header:

```
X-Slackclone-Signature: sha256=<hmac of the raw body with the shared secret>
```

`webhooks/utils.py` does the signing; the receiver recomputes the HMAC over the body
with the shared secret and compares — using **`hmac.compare_digest`** for a
constant-time check (so an attacker can't learn the signature byte-by-byte via
timing). A request without a valid signature is forged and must be rejected.

> The **secret is write-only** in the API serializer — you can set it, never read it
> back. Treat signing keys like passwords.

## 4. Decoupled with a signal

How does "any message created" trigger delivery without editing every create path
(REST, WebSocket, incoming webhook)? A **`post_save` signal** on `Message`
(`webhooks/signals.py`, connected in `apps.ready()`) calls `fire_message_created`,
which enqueues a Celery `deliver` task per subscribed webhook. One hook, every path
covered.

## 5. Reliable delivery (retries + audit)

External services go down. `deliver` is a Celery task with `max_retries=5` and
**exponential backoff**, and it records every attempt in `WebhookDelivery`
(status code, attempt number, success). So you get at-least-once delivery and a clear
audit trail when an integration misbehaves.

## 6. Slash commands (the same machinery)

A `/deploy staging` typed in chat is just a message your app can intercept and turn
into an outgoing call to a command's URL, then post the response back — incoming and
outgoing webhooks combined. You'll wire a simple one in the challenge.

---

## 7. Do the lab

Create an incoming webhook and post to it with `curl`; stand up a tiny local receiver
and register it as an outgoing webhook; post a message and watch the **signed**
delivery arrive; verify the signature; then knock the receiver offline and watch the
retries.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

incoming webhook · outgoing webhook · HMAC signature · constant-time compare · signal · retry/backoff

**Next →** [Module 09: Next.js Frontend Foundations](../09-nextjs-foundations/)

# Challenge 08 — Integrations That Don't Lie

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Reject forgeries.** Add an *inbound* signed webhook variant: a second incoming
   endpoint that requires a valid `X-Slackclone-Signature` over the raw body (using
   the webhook's stored secret) and returns `401` if it's wrong. Prove a tampered
   body is rejected.

2. **Don't loop.** An outgoing webhook fires on `message.created`. If an incoming
   webhook then posts a message, that *also* fires outgoing webhooks. Design and
   implement a guard so a message created **by** an incoming webhook does **not**
   trigger outgoing delivery (avoid infinite integration loops).

3. **Slash command.** Implement `/weather <city>`: when a message body starts with
   `/weather`, intercept it (don't store it as a normal message), call any public
   API (or stub it), and post the result back into the channel as a bot message.

4. **Delivery dashboard.** Add `GET /api/webhooks/outgoing/{id}/deliveries/` returning
   the recent `WebhookDelivery` records so an admin can see failures.

5. **Stretch:** Explain why we sign the **raw request body** (not a parsed/re-serialized
   version) and why the receiver must verify against the exact bytes it received.

## Success criteria
- [ ] A signed inbound endpoint rejects tampered payloads with `401`.
- [ ] Incoming-webhook messages don't trigger outgoing webhooks (no loop).
- [ ] `/weather` is intercepted and answered by a bot message.
- [ ] Admins can list delivery attempts for a webhook.
- [ ] You can explain raw-body signing.

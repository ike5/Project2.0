# Lab 06 — Presence, Rate Limits, and Unread Badges

**You'll:** observe presence keys appear and expire inside Redis, trip the message
rate limiter over a WebSocket, and watch unread counts grow and reset via the API.

⏱️ ~45 min. Redis + the ASGI server running. Reuse `$ACCESS`, `$WS`, `$CH` from
earlier labs.

---

## Part A — Watch presence in Redis

Open a Redis CLI alongside the running server:
```bash
docker compose -f ../00-setup/compose.dev.yml exec redis redis-cli
```
Connect a `wscat` client to a channel (from Lab 05). Then in the Redis CLI:
```
ZRANGE presence:online 0 -1 WITHSCORES     # your user id with a recent timestamp
```
✅ Expected: your user id appears with a score (a Unix timestamp).

Now **close** the `wscat` client and re-run `ZRANGE` after a moment:
✅ Expected: you're removed (the consumer called `go_offline`). Even without a clean
disconnect, the entry would age out after 30 s — try killing `wscat` with `Ctrl+C`
vs closing the terminal and compare.

---

## Part B — Heartbeats keep you online

With a `wscat` client connected, send periodically:
```json
{"type":"heartbeat"}
```
Each one refreshes your score (watch it tick up in `ZRANGE ... WITHSCORES`). This is
what the frontend does on a timer in Module 10 so you stay green while idle.

---

## Part C — Trip the rate limiter

The consumer allows 10 messages / 10 s per channel. In a `wscat` client, paste this
quickly, 11+ times:
```json
{"type":"message.new","body":"spam"}
```
✅ Expected: after ~10, you receive:
```json
{"type":"error","detail":"slow down"}
```
Confirm in Redis that a limiter key exists with a short TTL:
```
KEYS rl:*
TTL rl:msg:<your-user-id>:<channel-id>
```
✅ Expected: a key with a TTL counting down from 10.

---

## Part D — Unread counts

Post a few messages to `#general` from user **ann** (REST is fine):
```bash
for i in 1 2 3; do
  curl -s -H "Authorization: Bearer $ACCESS" -H 'content-type: application/json' \
    -X POST localhost:8000/api/messages/ -d "{\"channel\":$CH,\"body\":\"unread $i\"}" >/dev/null
done
```
As a **different** member (bob, after you add him to the channel), check unread:
```bash
curl -s -H "Authorization: Bearer $BOB" localhost:8000/api/channels/$CH/unread/ | jq
# {"unread": 3}
```
✅ Expected: a positive count.

Mark it read up to the latest message, then re-check:
```bash
LATEST=$(curl -s -H "Authorization: Bearer $BOB" "localhost:8000/api/messages/?channel=$CH" | jq '.results[0].id')
curl -s -H "Authorization: Bearer $BOB" -H 'content-type: application/json' \
  -X POST localhost:8000/api/channels/$CH/read/ -d "{\"message_id\":$LATEST}" >/dev/null
curl -s -H "Authorization: Bearer $BOB" localhost:8000/api/channels/$CH/unread/ | jq
# {"unread": 0}
```
✅ **Checkpoint:** reading the channel advanced `last_read` and cleared the badge.

---

## What you learned
- Presence is a Redis sorted set that self-expires — robust to crashes.
- Heartbeats keep a user "online"; the green dot is driven by live `presence` events.
- A 4-line Redis limiter caps message spam per channel.
- Unread counts stay cheap via a cached head id and a cache-busted COUNT.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 07](../07-celery-email-notifications/).

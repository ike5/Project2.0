# Module 06 — Presence & Caching with Redis

**Goal:** show who's online in real time, keep unread badges cheap, and rate-limit
abusive clients — all with Redis, not Postgres.

⏱️ ~2 hours · 🎯 Prereq: Module 05 (WebSockets working). Redis running.

> Some data is too hot or too ephemeral for a relational database. "Is Ann online?"
> changes every few seconds; counting unread messages on every page load would hammer
> Postgres. Redis is the right tool — and you already run it for the channel layer.

---

## 1. Three jobs, one Redis

`chat/presence.py` uses Redis for three things:

| Job | Redis structure | Why not Postgres |
|-----|-----------------|------------------|
| **Presence** | sorted set (`presence:online`) by timestamp | changes constantly; auto-expires |
| **Rate limiting** | counter with TTL (`rl:*`) | per-action, throwaway, must be fast |
| **Unread counts** | cached head id + cached COUNT | avoids a query on every page load |

## 2. Presence that expires on its own

A client is "online" only as long as it keeps **heartbeating**. We store each
online user in a **sorted set** scored by the last-seen timestamp:

```python
_redis.zadd("presence:online", {str(user_id): time.time()})
```

"Online" = score newer than `now - 30s`. If a browser crashes or a network drops,
no disconnect event may fire — but the score simply goes stale and the user falls
out of the online set automatically. That self-healing is why presence belongs in
Redis with a TTL mindset, not a boolean column.

The consumer calls `touch()` on connect and on **every inbound frame** (including an
explicit `heartbeat`), and `go_offline()` on disconnect, broadcasting a `presence`
event so other clients update the green dot live.

## 3. Rate limiting in 4 lines

A fixed-window limiter with `INCR` + `EXPIRE`:

```python
count = _redis.incr(key)
if count == 1: _redis.expire(key, window)
return count <= limit
```

The consumer caps each user to 10 messages / 10 s per channel; over that, the client
gets an `error` event instead of a stored message. (DRF's HTTP throttles from Module
03 use the same Redis under the hood.)

## 4. Unread counts: cheap by design

Naively, "how many unread in #general?" is `COUNT(*) WHERE id > last_read` on every
page load across every channel — expensive. We make it cheap two ways:

- **Cheap boolean:** we cache each channel's **newest message id** (`chan:head:*`).
  `has_unread = head > last_read` is a single Redis `GET`, perfect for the red dot.
- **Cached exact count:** when you do need the number, we `COUNT` once and cache it,
  **busting the cache** whenever a new message arrives in that channel.

> ⚠️ Message ids are a *global* sequence, so `head − last_read` is **not** a count
> (other channels' messages interleave the ids). That's why the exact count does a
> real `COUNT`, cached — see `unread_count()`.

`last_read` lives in Postgres on `ChannelMember.last_read_message_id`; the
`POST /api/channels/{id}/read/` action advances it when you view a channel.

## 5. Where each piece is called

```
connect ─────► presence.touch + broadcast "presence online"
inbound frame ► presence.touch (heartbeat)
message.new ──► rate-limit → save → presence.set_channel_head → broadcast
disconnect ───► presence.go_offline + broadcast "presence offline"
GET  /channels/{id}/unread/ ► presence.unread_count
POST /channels/{id}/read/   ► advance last_read
```

---

## 6. Do the lab

Watch presence appear and expire in Redis, trip the rate limiter, and see unread
counts update and reset as you read a channel.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

presence · TTL · sorted set · rate limiting · cache invalidation · unread count

**Next →** [Module 07: Celery — Email & Notifications](../07-celery-email-notifications/)

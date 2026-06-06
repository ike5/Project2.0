# Module 05 — Real-time with Django Channels

**Goal:** deliver messages instantly over WebSockets using Django Channels and a
Redis channel layer — authenticated, membership-checked, and ready to scale across
many backend Pods.

⏱️ ~3 hours · 🎯 Prereq: Module 04 (REST API + auth working). Redis running.

> This is the module that makes it feel like Slack. Until now, the frontend would
> have to poll for new messages. Now the server *pushes* them the instant they're posted.

---

## 1. WSGI → ASGI: why Django needs an upgrade

Classic Django (WSGI) is request/response: a client asks, the server answers, the
connection closes. A WebSocket stays **open** so the server can push at any time.
That needs **ASGI**, the async interface. `config/asgi.py` routes HTTP to normal
Django and `websocket` traffic to Channels:

```python
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})
```

## 2. Consumers: views for WebSockets

A **consumer** is to a WebSocket what a view is to HTTP. `ChannelConsumer` handles
three events:

- **`connect`** — authenticate, check the user may see this channel, then `group_add`.
- **`receive`** — parse the client's JSON (`message.new`, `typing`) and act.
- **`disconnect`** — `group_discard` (and mark away, in Module 06).

## 3. Groups + the channel layer (the scaling trick)

Every connection watching `#general` joins the **group** `channel_<id>`. To deliver
a message you `group_send` — and **every** connection in that group receives it,
even ones held by a *different* server process.

That cross-process magic is the **channel layer**, backed by **Redis**
(`channels_redis`). It's the same Redis you met in Module 00. Without it, a message
posted to Pod A would never reach a user connected to Pod B — which is exactly the
situation in Module 15 when you run 3 backend replicas.

```
 browser₁ ─ws─ Pod A ─┐                        ┌─ Pod B ─ws─ browser₂
                      ├─ Redis channel layer ──┤
 group_send("channel_1", msg) ── fans out to every Pod holding that group
```

## 4. Authenticating a WebSocket

Browsers can't set an `Authorization` header on a WebSocket, so the client appends
the access token as a query param: `ws://…/ws/channels/1/?token=<access>`.
`JWTAuthMiddleware` validates it and puts the `User` on `scope["user"]`; the consumer
rejects the connect (`close(4403)`) if the user is anonymous or not allowed.

## 5. Writing then broadcasting

On `message.new` the consumer:
1. writes the `Message` to Postgres (the source of truth), then
2. broadcasts the **server's** copy (real id + timestamp) to the group.

The sender receives it too, replacing its optimistic placeholder (Module 10). The
REST create path (`MessageViewSet.perform_create`) broadcasts through the *same*
`realtime.broadcast` helper — so a message posted by a webhook or the API also lights
up live clients.

## 6. Ephemeral events: typing

Not everything is stored. A `typing` event is fanned out to *others* in the group and
never written to the database — high-frequency, disposable, and excluded from the
sender's own socket.

---

## 7. Do the lab

Run the ASGI server, connect two WebSocket clients to the same channel, watch a
message from one appear in the other, see typing indicators, and confirm an
unauthenticated socket is rejected.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

WebSocket · ASGI · Channels · consumer · group · channel layer

**Next →** [Module 06: Presence & Caching with Redis](../06-redis-presence-cache/)

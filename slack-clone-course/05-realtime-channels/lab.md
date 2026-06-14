# Lab 05 — Live Messages over WebSockets

**You'll:** serve the app over ASGI, connect two WebSocket clients to the same
channel with `wscat`, send a message from one and watch it arrive in the other, try
typing indicators, and confirm auth is enforced.

⏱️ ~50 min. Redis must be running (`00-setup/compose.dev.yml`). You'll need a
channel id and an access token from earlier labs.

```bash
# install a WebSocket CLI client
npm install -g wscat
```

---

## Part A — Run the ASGI server

`runserver` already speaks ASGI because `daphne` is first in `INSTALLED_APPS`. For a
production-like run use uvicorn:

```bash
cd apps/slack-backend && source .venv/bin/activate
uvicorn config.asgi:application --reload --port 8000
```
✅ **Checkpoint:** the server starts and logs an ASGI/WebSocket-capable app.

---

## Part B — Get a token and a channel id

```bash
ACCESS=$(curl -s -X POST localhost:8000/api/auth/login/ -H 'content-type: application/json' \
  -d '{"email":"ann@example.com","password":"slackpass123"}' | jq -r .access)
WS=$(curl -s -H "Authorization: Bearer $ACCESS" localhost:8000/api/workspaces/ | jq '.[0].id')
CH=$(curl -s -H "Authorization: Bearer $ACCESS" "localhost:8000/api/channels/?workspace=$WS" \
  | jq '(.results // .)[0].id')
echo "channel=$CH"
```

---

## Part C — Two clients, one channel

Open **two** terminals. In each, connect to the same channel:
```bash
wscat -c "ws://localhost:8000/ws/channels/$CH/?token=$ACCESS"
```
✅ Both connect (no immediate close). In **terminal 1**, send:
```json
{"type":"message.new","body":"hello from terminal 1"}
```
✅ Expected: **both** terminals receive:
```json
{"type":"message.new","id":...,"channel":...,"body":"hello from terminal 1","author":{"username":"ann"},...}
```
The message now also exists in Postgres — confirm over REST:
```bash
curl -s -H "Authorization: Bearer $ACCESS" "localhost:8000/api/messages/?channel=$CH" \
  | jq '.results[0].body'
```
✅ **Checkpoint:** the live broadcast and the stored history agree — same message, real id.

---

## Part D — Typing indicators (ephemeral)

In terminal 1:
```json
{"type":"typing"}
```
✅ Expected: terminal 2 receives `{"type":"typing","user":"ann",...}`, but terminal
1 does **not** (the sender is excluded). Nothing is written to the database.

---

## Part E — Auth is enforced

```bash
# no token → rejected
wscat -c "ws://localhost:8000/ws/channels/$CH/"
# garbage token → rejected
wscat -c "ws://localhost:8000/ws/channels/$CH/?token=not-a-real-token"
```
✅ Expected: the socket closes immediately (code 4403). Only authenticated members
of the channel can connect.

---

## Part F — Prove the cross-process bus (optional)

Run a **second** server on port 8001 against the same Redis, connect one `wscat` to
each port, and send from one. The message still arrives on the other — because the
Redis channel layer fanned it across processes. This is exactly what makes 3 replicas
work in Module 15.

---

## What you learned
- ASGI + Channels add a `websocket` protocol alongside HTTP.
- A consumer authenticates, joins a group, and broadcasts via the channel layer.
- The Redis channel layer delivers across processes — the basis for scaling.
- Stored messages and live broadcasts stay consistent; typing is ephemeral.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 06](../06-redis-presence-cache/).

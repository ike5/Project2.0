# Cheatsheet — Channels & WebSockets

## Mental model

```
client ──ws──► ASGI ──► consumer (connect/receive/disconnect)
                         │ group_add / group_send
                         ▼
                   Redis channel layer  ── fans out to every pod ──► other sockets
```

- **channel_name** = one connection. **group** = many connections you broadcast to.
- The Redis channel layer is what makes broadcasts cross processes/pods.

## Consumer skeleton (async)

```python
class ChannelConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated: return await self.close(4403)
        self.group = f"channel_{self.channel_id}"
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()
    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)
    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        await self.channel_layer.group_send(self.group,
            {"type": "broadcast.event", "event": {...}})
    async def broadcast_event(self, message):     # handler for type "broadcast.event"
        await self.send(text_data=json.dumps(message["event"]))
```

## Sync ORM inside async

```python
from channels.db import database_sync_to_async

@database_sync_to_async
def _save(self): return Message.objects.create(...)
```

## Broadcast from sync code (REST view, Celery, signal)

```python
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
async_to_sync(get_channel_layer().group_send)("channel_1",
    {"type": "broadcast.event", "event": {...}})
```

## Routing + ASGI

```python
# routing.py
websocket_urlpatterns = [re_path(r"ws/channels/(?P<channel_id>\d+)/$", ChannelConsumer.as_asgi())]
# asgi.py
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})
```

## Auth over WebSocket (token in query)

```
ws://host/ws/channels/1/?token=<access>
```
Middleware reads `query_string`, validates the JWT, sets `scope["user"]`.

## Testing

```bash
npm i -g wscat
wscat -c "ws://localhost:8000/ws/channels/1/?token=$ACCESS"
> {"type":"message.new","body":"hi"}
```
```python
# pytest
from channels.testing import WebsocketCommunicator
comm = WebsocketCommunicator(application, f"/ws/channels/{id}/?token={t}")
ok, _ = await comm.connect()
```

## Run an ASGI server

```bash
uvicorn config.asgi:application --reload --port 8000
# prod: gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker -w 3
```

## Gotchas
- In-memory channel layer **doesn't** cross processes — use `channels_redis` in prod.
- `group_send` "type" maps to a consumer method with dots→underscores
  (`broadcast.event` → `broadcast_event`).
- Browsers can't set headers on WS → pass the token as a query param.

# Challenge 05 — Reference Solution

### 1. Edit & delete, live
```python
# chat/consumers.py — in receive()
elif kind == "message.edit":
    msg = await self._edit_message(data["id"], (data.get("body") or "").strip())
    if msg:
        await self.channel_layer.group_send(self.group, {
            "type": "broadcast.event",
            "event": {"type": "message.updated", "id": msg.id, "body": msg.body},
        })

elif kind == "message.delete":
    if await self._delete_message(data["id"]):
        await self.channel_layer.group_send(self.group, {
            "type": "broadcast.event",
            "event": {"type": "message.deleted", "id": data["id"]},
        })
```
```python
from django.utils import timezone

@database_sync_to_async
def _edit_message(self, mid, body):
    m = Message.objects.filter(id=mid, channel_id=self.channel_id, author=self.user).first()
    if not m or not body:
        return None
    m.body = body; m.edited_at = timezone.now(); m.save(update_fields=["body", "edited_at"])
    return m

@database_sync_to_async
def _delete_message(self, mid):
    return Message.objects.filter(id=mid, channel_id=self.channel_id, author=self.user).delete()[0] > 0
```

### 2. Reactions, live
```python
elif kind == "reaction.add":
    ok = await self._add_reaction(data["id"], data.get("emoji", ""))
    if ok:
        await self.channel_layer.group_send(self.group, {
            "type": "broadcast.event",
            "event": {"type": "reaction.added", "message": data["id"],
                      "emoji": data["emoji"], "user": self.user.username},
        })
```
```python
@database_sync_to_async
def _add_reaction(self, mid, emoji):
    from django.db import IntegrityError
    from .models import Reaction
    if not emoji:
        return False
    try:
        Reaction.objects.create(message_id=mid, user=self.user, emoji=emoji)
    except IntegrityError:
        return False
    return True
```

### 3. Private-channel rejection (test)
The existing `_can_access` already returns `False` for a private channel the user
isn't a member of, so `connect` closes with 4403. A test:
```python
async def test_private_rejected(...):
    # ch.kind = "private", user NOT a ChannelMember
    comm = WebsocketCommunicator(application, f"/ws/channels/{ch.id}/?token={token}")
    connected, _ = await comm.connect()
    assert connected is False
```

### 4. Limit message size
```python
if kind == "message.new":
    body = (data.get("body") or "").strip()
    if len(body) > 4000:
        await self.send(text_data=json.dumps({"type": "error", "detail": "message too long"}))
        return
    ...
```

### 5. Two tabs
> Each tab opens its **own** WebSocket connection, and both join the same group
> `channel_<id>`. When the user posts, the consumer does one `group_send`, and the
> channel layer delivers it to *every* connection in the group — which includes both
> of this user's tabs. So the message appears in both, exactly like it does for other
> members. (Each connection is a distinct `channel_name`; the group is the fan-out unit.)

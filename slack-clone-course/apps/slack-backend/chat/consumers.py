"""
The WebSocket consumer for a single channel.

Lifecycle:
- connect:    authenticate (JWT middleware set scope["user"]), verify the user may
              see this channel, then join the channel's group.
- receive:    handle client events — new message, typing indicator.
- disconnect: leave the group (and mark away in Module 06).

New messages are written to Postgres and broadcast to the group, so every connected
client — even ones served by a *different* backend Pod — receives them via Redis.
"""
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Channel, Message
from .realtime import channel_group, serialize_message


class ChannelConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.channel_id = int(self.scope["url_route"]["kwargs"]["channel_id"])

        if not self.user.is_authenticated or not await self._can_access():
            await self.close(code=4403)   # policy violation
            return

        self.group = channel_group(self.channel_id)
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data or "{}")
        kind = data.get("type")

        if kind == "message.new":
            body = (data.get("body") or "").strip()
            if not body:
                return
            message = await self._create_message(body, data.get("parent"))
            # Broadcast to everyone in the channel (including the sender, for the
            # authoritative server copy with a real id and timestamp).
            await self.channel_layer.group_send(
                self.group,
                {"type": "broadcast.event", "event": serialize_message(message)},
            )

        elif kind == "typing":
            # Ephemeral — never stored. Just fan out to others.
            await self.channel_layer.group_send(
                self.group,
                {
                    "type": "broadcast.event",
                    "event": {
                        "type": "typing",
                        "channel": self.channel_id,
                        "user": self.user.username,
                    },
                    "exclude": self.channel_name,
                },
            )

    async def broadcast_event(self, message):
        """Group handler: push an event down this socket (unless excluded)."""
        if message.get("exclude") == self.channel_name:
            return
        await self.send(text_data=json.dumps(message["event"]))

    # ── DB helpers (sync ORM wrapped for async) ───────────────────────────────
    @database_sync_to_async
    def _can_access(self) -> bool:
        from workspaces.permissions import is_member

        channel = Channel.objects.filter(id=self.channel_id).first()
        if not channel or not is_member(self.user, channel.workspace_id):
            return False
        if channel.kind == "public":
            return True
        return channel.members.filter(pk=self.user.pk).exists()

    @database_sync_to_async
    def _create_message(self, body, parent_id):
        msg = Message.objects.create(
            channel_id=self.channel_id,
            author=self.user,
            parent_id=parent_id,
            body=body,
        )
        # Re-fetch with author for serialization.
        return Message.objects.select_related("author").get(pk=msg.pk)

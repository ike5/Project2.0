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

        # Presence: mark online and tell the channel.
        from . import presence

        presence.touch(self.user.id)
        await self._broadcast_presence(online=True)

    async def disconnect(self, code):
        if hasattr(self, "group"):
            from . import presence

            presence.go_offline(self.user.id)
            await self._broadcast_presence(online=False)
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def _broadcast_presence(self, online: bool):
        await self.channel_layer.group_send(
            self.group,
            {
                "type": "broadcast.event",
                "event": {
                    "type": "presence",
                    "user": self.user.username,
                    "online": online,
                },
            },
        )

    async def receive(self, text_data=None, bytes_data=None):
        from . import presence

        data = json.loads(text_data or "{}")
        kind = data.get("type")

        # Any inbound frame counts as a heartbeat (keeps presence fresh).
        presence.touch(self.user.id)

        if kind == "heartbeat":
            return  # presence already refreshed above

        if kind == "message.new":
            body = (data.get("body") or "").strip()
            if not body:
                return
            # Rate-limit: at most 10 messages / 10s per user per channel.
            if not presence.allow(f"msg:{self.user.id}:{self.channel_id}", limit=10, window=10):
                await self.send(text_data=json.dumps(
                    {"type": "error", "detail": "slow down"}))
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
        from . import presence

        msg = Message.objects.create(
            channel_id=self.channel_id,
            author=self.user,
            parent_id=parent_id,
            body=body,
        )
        # Track the channel's newest message id for cheap unread counts (Module 06).
        presence.set_channel_head(self.channel_id, msg.id)
        # Async notification fan-out (mentions/DM → in-app + email) (Module 07).
        from notifications.services import on_new_message

        on_new_message(msg.id)
        # Re-fetch with author for serialization.
        return Message.objects.select_related("author").get(pk=msg.pk)

"""
Helpers for broadcasting over the Channels channel layer.

Centralized here so the consumer, the REST viewset, webhooks (Module 08), and Celery
tasks (Module 07) all broadcast through one consistent path.
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def channel_group(channel_id) -> str:
    """The group name every connection watching a channel joins."""
    return f"channel_{channel_id}"


def broadcast(channel_id, event: dict) -> None:
    """Send `event` to everyone in a channel's group (callable from sync code)."""
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        channel_group(channel_id),
        {"type": "broadcast.event", "event": event},
    )


def serialize_message(message) -> dict:
    """A compact wire format for a message (matches the frontend's expectations)."""
    return {
        "type": "message.new",
        "id": message.id,
        "channel": message.channel_id,
        "parent": message.parent_id,
        "body": message.body,
        "author": {
            "id": message.author_id,
            "username": message.author.username,
        },
        "created_at": message.created_at.isoformat(),
    }

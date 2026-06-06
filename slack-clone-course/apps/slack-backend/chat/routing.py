"""
WebSocket URL routes for Channels.

Empty until Module 05, where we add the ChannelConsumer at
ws/channels/<id>/ and the JWT auth middleware.
"""
from django.urls import re_path

websocket_urlpatterns: list = [
    # Module 05 adds:
    # re_path(r"ws/channels/(?P<channel_id>\d+)/$", ChannelConsumer.as_asgi()),
]

# Keep the import used once routes exist.
__all__ = ["websocket_urlpatterns", "re_path"]

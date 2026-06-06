"""WebSocket URL routes for Channels (wired into config/asgi.py)."""
from django.urls import re_path

from .consumers import ChannelConsumer

websocket_urlpatterns = [
    re_path(r"ws/channels/(?P<channel_id>\d+)/$", ChannelConsumer.as_asgi()),
]

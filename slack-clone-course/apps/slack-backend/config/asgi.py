"""
ASGI entrypoint. Routes HTTP to Django and WebSocket traffic to Channels.

In Module 02 only the HTTP path matters. Module 05 fills in chat/routing.py with
the WebSocket URL patterns and JWT auth middleware so the `websocket` branch lights up.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Initialize Django (loads apps) before importing anything that touches models.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from chat.routing import websocket_urlpatterns  # noqa: E402

try:
    # JWTAuthMiddleware is added in Module 05.
    from chat.middleware import JWTAuthMiddlewareStack

    websocket_app = JWTAuthMiddlewareStack(URLRouter(websocket_urlpatterns))
except ImportError:
    websocket_app = URLRouter(websocket_urlpatterns)

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": websocket_app,
    }
)

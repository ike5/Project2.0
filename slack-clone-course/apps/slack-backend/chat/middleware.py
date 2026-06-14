"""
JWT authentication for WebSocket connections.

Browsers can't set Authorization headers on a WebSocket, so the client passes the
access token as a query param: ws://host/ws/channels/1/?token=<access>. This
middleware validates it and attaches the user to the connection scope.
"""
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        token = self._token_from_scope(scope)
        scope["user"] = AnonymousUser()
        if token:
            try:
                payload = AccessToken(token)
                scope["user"] = await get_user(payload["user_id"])
            except TokenError:
                pass  # leave AnonymousUser; the consumer will reject the connect
        return await super().__call__(scope, receive, send)

    @staticmethod
    def _token_from_scope(scope):
        query = scope.get("query_string", b"").decode()
        for part in query.split("&"):
            if part.startswith("token="):
                return part.split("=", 1)[1]
        return None


def JWTAuthMiddlewareStack(inner):
    # Fall back to session auth too (handy for the admin/browsable API).
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))

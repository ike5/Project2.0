"""
Incoming webhooks (external → us) and management of incoming/outgoing webhooks.

Incoming: a tokened, public URL that posts a message into one channel. No JWT — the
secret token *is* the credential, so treat the URL like a password.
"""
import secrets

from rest_framework import mixins, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import Message
from chat.presence import set_channel_head
from chat.realtime import broadcast, serialize_message
from notifications.services import on_new_message
from workspaces.models import Membership

from .models import IncomingWebhook, OutgoingWebhook
from .serializers import IncomingWebhookSerializer, OutgoingWebhookSerializer


class IncomingWebhookView(APIView):
    """POST /api/webhooks/in/<token>/  body: {"text": "..."} → posts to the channel."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []   # token in the URL is the credential

    def post(self, request, token):
        hook = IncomingWebhook.objects.filter(token=token, active=True).first()
        if not hook:
            return Response({"detail": "unknown webhook"}, status=404)
        text = (request.data.get("text") or "").strip()
        if not text:
            return Response({"detail": "text required"}, status=400)

        # The webhook's creator is recorded as the author (a real user).
        message = Message.objects.create(
            channel=hook.channel, author_id=hook.created_by_id, body=text
        )
        # Same post-create effects as a normal message.
        set_channel_head(message.channel_id, message.id)
        message = Message.objects.select_related("author").get(pk=message.pk)
        broadcast(message.channel_id, serialize_message(message))
        on_new_message(message.id)
        return Response({"ok": True, "message_id": message.id}, status=201)


class _WorkspaceAdminScoped:
    """Mixin: limit management to workspaces where the user is owner/admin."""

    def _admin_workspace_ids(self):
        return Membership.objects.filter(
            user=self.request.user, role__in=["owner", "admin"]
        ).values_list("workspace_id", flat=True)


class IncomingWebhookViewSet(_WorkspaceAdminScoped, viewsets.ModelViewSet):
    serializer_class = IncomingWebhookSerializer

    def get_queryset(self):
        return IncomingWebhook.objects.filter(
            channel__workspace_id__in=self._admin_workspace_ids()
        )

    def perform_create(self, serializer):
        serializer.save(token=secrets.token_urlsafe(24), created_by=self.request.user)


class OutgoingWebhookViewSet(_WorkspaceAdminScoped, viewsets.ModelViewSet):
    serializer_class = OutgoingWebhookSerializer

    def get_queryset(self):
        return OutgoingWebhook.objects.filter(workspace_id__in=self._admin_workspace_ids())

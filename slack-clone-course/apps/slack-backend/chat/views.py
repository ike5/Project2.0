"""
Channel and Message REST API.

Reads (history) go over REST with cursor pagination; live delivery is the WebSocket
consumer in Module 05. Creating a message here also works, and Module 05 has the
consumer broadcast it — so REST and WebSocket stay consistent.
"""
from django.db.models import Q
from rest_framework import mixins, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import CursorPagination

from workspaces.models import Membership
from workspaces.permissions import IsWorkspaceMember, is_member

from .models import Channel, Message
from .serializers import ChannelSerializer, MessageSerializer


class ChannelViewSet(viewsets.ModelViewSet):
    serializer_class = ChannelSerializer
    permission_classes = [IsWorkspaceMember]
    filterset_fields = ["workspace", "kind"]

    def get_queryset(self):
        # Channels in workspaces the user belongs to. Private/DM channels also
        # require the user to be a channel member.
        my_ws = Membership.objects.filter(user=self.request.user).values_list(
            "workspace_id", flat=True
        )
        return (
            Channel.objects.filter(workspace_id__in=my_ws)
            .filter(Q(kind="public") | Q(members=self.request.user))
            .distinct()
            .order_by("name")
        )

    def perform_create(self, serializer):
        workspace = serializer.validated_data["workspace"]
        if not is_member(self.request.user, workspace.id):
            raise PermissionDenied("Not a member of that workspace.")
        serializer.save(created_by=self.request.user)


class MessageCursorPagination(CursorPagination):
    # Stable pagination over an ever-growing feed: order by id, newest first.
    page_size = 30
    ordering = "-id"


class MessageViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = MessageSerializer
    pagination_class = MessageCursorPagination
    filterset_fields = ["channel", "parent"]

    def get_queryset(self):
        # Only messages in channels the user can see.
        visible_channels = ChannelViewSet.get_queryset(self)  # reuse the same rule
        return (
            Message.objects.filter(channel__in=visible_channels)
            .select_related("author")
            .prefetch_related("reactions")
        )

    def perform_create(self, serializer):
        channel = serializer.validated_data["channel"]
        user = self.request.user
        # Must belong to the workspace; private/DM channels also require membership.
        allowed = is_member(user, channel.workspace_id) and (
            channel.kind == "public" or channel.members.filter(pk=user.pk).exists()
        )
        if not allowed:
            raise PermissionDenied("You can't post to that channel.")
        message = serializer.save(author=user)
        # Keep REST and WebSocket consistent: a message created over REST is
        # broadcast to all live clients too (Module 05).
        from .realtime import broadcast, serialize_message

        broadcast(message.channel_id, serialize_message(message))

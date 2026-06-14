"""List your notifications and mark them read."""
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        # You only ever see your own notifications.
        qs = Notification.objects.filter(user=self.request.user)
        if self.request.query_params.get("unread") == "true":
            qs = qs.filter(read=False)
        return qs

    @action(detail=False, methods=["post"])
    def read_all(self, request):
        n = Notification.objects.filter(user=request.user, read=False).update(read=True)
        return Response({"marked_read": n})

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        notif = self.get_object()
        notif.read = True
        notif.save(update_fields=["read"])
        return Response({"ok": True})

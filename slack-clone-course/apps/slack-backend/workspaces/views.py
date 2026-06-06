"""Workspace API: list the workspaces you belong to, create one, view members."""
from django.db import transaction
from rest_framework import decorators, mixins, response, viewsets

from .models import Membership, Workspace
from .permissions import IsWorkspaceMember
from .serializers import MembershipSerializer, WorkspaceSerializer


class WorkspaceViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsWorkspaceMember]

    def get_queryset(self):
        # Only workspaces the user is a member of — multi-tenant isolation.
        memberships = Membership.objects.filter(user=self.request.user)
        role_by_ws = {m.workspace_id: m.role for m in memberships}
        qs = Workspace.objects.filter(id__in=role_by_ws.keys()).order_by("name")
        for w in qs:
            w._my_role = role_by_ws.get(w.id)
        return qs

    def perform_create(self, serializer):
        # Creating a workspace makes you its owner, atomically.
        with transaction.atomic():
            workspace = serializer.save()
            Membership.objects.create(
                user=self.request.user, workspace=workspace, role=Membership.Role.OWNER
            )
            workspace._my_role = Membership.Role.OWNER

    @decorators.action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        ws = self.get_object()
        qs = Membership.objects.filter(workspace=ws).select_related("user")
        return response.Response(MembershipSerializer(qs, many=True).data)

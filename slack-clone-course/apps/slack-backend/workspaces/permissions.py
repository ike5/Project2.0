"""
Reusable permission classes for workspace-scoped access.

These are the heart of multi-tenant safety: a logged-in user may only touch data in
workspaces they belong to. Used by the viewsets in Module 04 and the consumer in
Module 05.
"""
from rest_framework.permissions import BasePermission

from .models import Membership


def is_member(user, workspace_id) -> bool:
    """True if `user` has a membership in the given workspace."""
    if not user or not user.is_authenticated:
        return False
    return Membership.objects.filter(user=user, workspace_id=workspace_id).exists()


def role_of(user, workspace_id):
    """Return the user's role string in a workspace, or None."""
    m = Membership.objects.filter(user=user, workspace_id=workspace_id).first()
    return m.role if m else None


class IsWorkspaceMember(BasePermission):
    """Object-level check: the request user must be a member of obj's workspace.

    Works for any object that exposes a `workspace_id` (Channel, Message via its
    channel, etc.). Viewsets also filter the queryset by membership so non-members
    never even see the objects — this is the second line of defense.
    """

    message = "You are not a member of this workspace."

    def has_object_permission(self, request, view, obj):
        workspace_id = getattr(obj, "workspace_id", None)
        if workspace_id is None and hasattr(obj, "channel"):
            workspace_id = obj.channel.workspace_id
        return is_member(request.user, workspace_id)


class IsWorkspaceAdmin(BasePermission):
    """Owner or admin of the workspace (for destructive/management actions)."""

    message = "Requires workspace admin or owner."

    def has_object_permission(self, request, view, obj):
        workspace_id = getattr(obj, "workspace_id", None)
        if workspace_id is None and hasattr(obj, "channel"):
            workspace_id = obj.channel.workspace_id
        return role_of(request.user, workspace_id) in {"owner", "admin"}

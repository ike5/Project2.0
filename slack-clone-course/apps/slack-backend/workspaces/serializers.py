from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Membership, Workspace


class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ("id", "user", "role", "joined_at")


class WorkspaceSerializer(serializers.ModelSerializer):
    my_role = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = ("id", "name", "slug", "created_at", "my_role")
        read_only_fields = ("id", "created_at", "my_role")

    def get_my_role(self, obj):
        # Annotated by the viewset (avoids an extra query per row).
        return getattr(obj, "_my_role", None)

from rest_framework import serializers

from .models import IncomingWebhook, OutgoingWebhook


class IncomingWebhookSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = IncomingWebhook
        fields = ("id", "channel", "label", "token", "active", "url", "created_at")
        read_only_fields = ("id", "token", "url", "created_at")

    def get_url(self, obj):
        return f"/api/webhooks/in/{obj.token}/"


class OutgoingWebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutgoingWebhook
        fields = ("id", "workspace", "target_url", "secret", "event", "active", "created_at")
        read_only_fields = ("id", "created_at")
        extra_kwargs = {"secret": {"write_only": True}}   # never expose the signing key

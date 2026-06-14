from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Channel, Message, Reaction


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ("id", "workspace", "name", "topic", "kind", "created_at")
        read_only_fields = ("id", "created_at")


class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = ("id", "emoji", "user")
        read_only_fields = ("id", "user")


class MessageSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    reactions = ReactionSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = (
            "id", "channel", "author", "parent", "body",
            "created_at", "edited_at", "reactions",
        )
        read_only_fields = ("id", "author", "created_at", "edited_at", "reactions")

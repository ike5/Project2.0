"""
Channels, channel membership, messages, reactions, attachments.

Key design decisions (from Module 01):
- A DM is just a Channel with kind="dm" and no name → one uniform message path.
- A thread is a Message whose `parent` points at the message it replies to.
- `ChannelMember.last_read_message_id` powers unread counts (Module 06).
"""
from django.conf import settings
from django.db import models

from workspaces.models import Workspace


class Channel(models.Model):
    class Kind(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"
        DM = "dm", "Direct message"

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="channels")
    name = models.CharField(max_length=80, blank=True, null=True)   # null for DMs
    topic = models.CharField(max_length=255, blank=True)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.PUBLIC)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="ChannelMember", related_name="channels"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["workspace", "name"], name="uniq_channel_name_per_workspace"
            )
        ]

    def __str__(self):
        return f"#{self.name}" if self.name else f"DM:{self.pk}"


class ChannelMember(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # The id of the newest message this user has read — drives unread counts.
    last_read_message_id = models.BigIntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["channel", "user"], name="uniq_channel_member"
            )
        ]


class Message(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies"
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            # The hot query: a channel's messages newest-first (history + pagination).
            models.Index(fields=["channel", "-id"]),
        ]
        ordering = ["id"]

    def __str__(self):
        return f"{self.author}: {self.body[:30]}"


class Reaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=32)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["message", "user", "emoji"], name="uniq_reaction"
            )
        ]


class Attachment(models.Model):
    """Metadata for a file in object storage (the bytes live in MinIO/S3, Module 11)."""
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="attachments", null=True, blank=True
    )
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    key = models.CharField(max_length=512)            # object-storage key
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120)
    size = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

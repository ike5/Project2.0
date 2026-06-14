"""In-app notifications. Created by Celery tasks (Module 07) when you're @mentioned
or DM'd; the frontend lists unread ones."""
from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Kind(models.TextChoices):
        MENTION = "mention", "Mention"
        DM = "dm", "Direct message"
        INVITE = "invite", "Workspace invite"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    kind = models.CharField(max_length=12, choices=Kind.choices)
    # Loose reference to the source object (a message id, invite id, …).
    payload = models.JSONField(default=dict)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["user", "read", "-id"])]
        ordering = ["-id"]

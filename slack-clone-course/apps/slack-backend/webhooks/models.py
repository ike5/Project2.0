"""
Incoming and outgoing webhooks (built in Module 08).

- IncomingWebhook: a secret-tokened URL external tools POST to, to post a message
  into one channel.
- OutgoingWebhook: a URL we POST events to (e.g. message.created), signed with HMAC.
"""
from django.conf import settings
from django.db import models

from chat.models import Channel
from workspaces.models import Workspace


class IncomingWebhook(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name="incoming_webhooks")
    token = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=120, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)


class OutgoingWebhook(models.Model):
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name="outgoing_webhooks")
    target_url = models.URLField()
    secret = models.CharField(max_length=64)          # HMAC signing key
    event = models.CharField(max_length=40, default="message.created")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class WebhookDelivery(models.Model):
    """Audit/retry record for an outgoing delivery attempt (Celery, Module 08)."""
    webhook = models.ForeignKey(OutgoingWebhook, on_delete=models.CASCADE, related_name="deliveries")
    status_code = models.IntegerField(null=True)
    attempt = models.IntegerField(default=1)
    succeeded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

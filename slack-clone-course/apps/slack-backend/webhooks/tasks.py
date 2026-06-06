"""
Outgoing webhook delivery (Celery).

When a message is created, we POST a signed JSON payload to every active outgoing
webhook subscribed to `message.created` in that workspace. Delivery is retried with
backoff and recorded for auditing.
"""
import json

import requests
from celery import shared_task

from .models import OutgoingWebhook, WebhookDelivery
from .utils import SIGNATURE_HEADER, sign


@shared_task(bind=True, max_retries=5, default_retry_delay=10)
def deliver(self, webhook_id: int, payload: dict):
    hook = OutgoingWebhook.objects.filter(id=webhook_id, active=True).first()
    if not hook:
        return

    body = json.dumps(payload, separators=(",", ":")).encode()
    headers = {
        "Content-Type": "application/json",
        SIGNATURE_HEADER: sign(hook.secret, body),   # receiver verifies this
    }
    attempt = self.request.retries + 1
    try:
        resp = requests.post(hook.target_url, data=body, headers=headers, timeout=5)
        WebhookDelivery.objects.create(
            webhook=hook, status_code=resp.status_code,
            attempt=attempt, succeeded=resp.ok,
        )
        if not resp.ok:
            raise RuntimeError(f"non-2xx: {resp.status_code}")
    except Exception as exc:  # noqa: BLE001 — network errors etc.
        WebhookDelivery.objects.create(
            webhook=hook, status_code=None, attempt=attempt, succeeded=False
        )
        # Exponential backoff: 10s, 20s, 40s, 80s, 160s.
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 10)


def fire_message_created(message):
    """Enqueue delivery to every subscribed outgoing webhook (called from a signal)."""
    payload = {
        "event": "message.created",
        "channel": message.channel_id,
        "message_id": message.id,
        "author": message.author.username,
        "body": message.body,
    }
    hooks = OutgoingWebhook.objects.filter(
        workspace_id=message.channel.workspace_id,
        event="message.created",
        active=True,
    ).values_list("id", flat=True)
    for hook_id in hooks:
        deliver.delay(hook_id, payload)

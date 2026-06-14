"""
Fire outgoing webhooks whenever a Message is created — regardless of whether it came
from the REST API, a WebSocket, or an incoming webhook. A signal keeps this decoupled
from the message-creation code.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from chat.models import Message

from .tasks import fire_message_created


@receiver(post_save, sender=Message, dispatch_uid="webhooks_message_created")
def on_message_saved(sender, instance, created, **kwargs):
    if created:
        fire_message_created(instance)

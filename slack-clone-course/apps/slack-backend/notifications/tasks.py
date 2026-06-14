"""
Celery tasks: notification fan-out, email, and the periodic digest.

Design notes:
- Tasks are **idempotent** where it matters (get_or_create on Notification) because
  Celery may retry a task after a transient failure.
- Email sending is retried with backoff on failure.
- Heavy work (looping over recipients, SMTP) runs here, never in the request cycle.
"""
from celery import shared_task
from django.core.mail import send_mail

from .models import Notification


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_email(self, subject: str, body: str, to: str):
    """Send one email; retry with backoff on transient SMTP errors."""
    try:
        send_mail(subject, body, None, [to], fail_silently=False)
    except Exception as exc:  # noqa: BLE001 — retry any transient failure
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 10)


@shared_task
def fan_out_message(message_id: int):
    """Create in-app notifications and emails for a new message's recipients."""
    from chat.models import Channel, ChannelMember, Message
    from chat.presence import is_online
    from accounts.models import User
    from .services import extract_mentions

    message = (
        Message.objects.select_related("channel", "author")
        .filter(id=message_id)
        .first()
    )
    if not message:
        return
    channel: Channel = message.channel

    # Who should be notified?
    if channel.kind == "dm":
        # Everyone in the DM except the sender.
        recipient_ids = ChannelMember.objects.filter(channel=channel) \
            .exclude(user=message.author).values_list("user_id", flat=True)
        kind = Notification.Kind.DM
        mentioned = set()
    else:
        # Only @mentioned members of the channel's workspace.
        handles = extract_mentions(message.body)
        if not handles:
            return
        mentioned = set(
            User.objects.filter(username__in=handles)
            .exclude(id=message.author_id)
            .values_list("id", flat=True)
        )
        recipient_ids = mentioned
        kind = Notification.Kind.MENTION

    for uid in recipient_ids:
        # Idempotent: the same fan-out re-run won't duplicate the notification.
        notif, created = Notification.objects.get_or_create(
            user_id=uid,
            kind=kind,
            payload={"message": message.id, "channel": channel.id},
        )
        # Email only if the user isn't actively online (don't spam active users).
        if created and not is_online(uid):
            user = User.objects.get(id=uid)
            label = f"#{channel.name}" if channel.name else "a direct message"
            send_email.delay(
                subject=f"New {'mention' if kind == 'mention' else 'message'} in {label}",
                body=f"{message.author.username}: {message.body}",
                to=user.email,
            )


@shared_task
def send_invite_email(invite_id: int):
    from workspaces.models import Invite

    invite = Invite.objects.select_related("workspace").filter(id=invite_id).first()
    if not invite:
        return
    link = f"/invite/accept?token={invite.token}"
    send_email.delay(
        subject=f"You're invited to {invite.workspace.name}",
        body=f"Join {invite.workspace.name} on Slack Clone: {link}",
        to=invite.email,
    )


@shared_task
def send_daily_digest():
    """Periodic (Celery Beat): email each user a summary of unread notifications."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    for user in User.objects.filter(notifications__read=False).distinct():
        count = user.notifications.filter(read=False).count()
        if count:
            send_email.delay(
                subject="Your Slack Clone digest",
                body=f"You have {count} unread notifications.",
                to=user.email,
            )

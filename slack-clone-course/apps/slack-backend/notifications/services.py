"""
Notification orchestration (sync, fast) — decides *what* should happen, then hands
the slow work (DB writes for many users, email) to Celery.

Called from both the WebSocket consumer and the REST create path whenever a message
is posted, so notifications fire no matter how a message arrived.
"""
import re

# @handle — letters, digits, underscore, dot, hyphen.
MENTION_RE = re.compile(r"(?<![\w/])@([\w.\-]+)")


def extract_mentions(body: str) -> set[str]:
    """Usernames mentioned in a message body, e.g. '@ann hi @bob' → {'ann','bob'}."""
    return {m.lower() for m in MENTION_RE.findall(body or "")}


def on_new_message(message_id: int) -> None:
    """Entry point after a message is saved. Enqueues async fan-out."""
    # Import inside the function so importing services doesn't require Celery/broker.
    from .tasks import fan_out_message

    fan_out_message.delay(message_id)

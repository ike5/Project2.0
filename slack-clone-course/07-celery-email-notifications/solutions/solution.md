# Challenge 07 — Reference Solution

### 1. Welcome email on signup
```python
# notifications/tasks.py
@shared_task
def send_welcome_email(user_id: int):
    from accounts.models import User
    u = User.objects.get(id=user_id)
    send_email.delay("Welcome to Slack Clone", f"Hi {u.username}!", u.email)
```
```python
# accounts/views.py — RegisterView
from django.db import transaction
from notifications.tasks import send_welcome_email

def perform_create(self, serializer):
    user = serializer.save()
    transaction.on_commit(lambda: send_welcome_email.delay(user.id))
```

### 2. Invite flow
```python
# workspaces/views.py — an invite action / serializer create:
from django.db import transaction
from notifications.tasks import send_invite_email

invite = Invite.objects.create(workspace=ws, email=email, token=secrets.token_urlsafe(24),
                               invited_by=request.user)
transaction.on_commit(lambda: send_invite_email.delay(invite.id))
```
`send_invite_email` (already in `tasks.py`) builds the body with
`/invite/accept?token=<token>`.

### 3. Don't notify yourself
Already handled: `fan_out_message` excludes the author —
`.exclude(id=message.author_id)` for mentions, and DM recipients
`.exclude(user=message.author)`. A test:
```python
m = Message.objects.create(channel=ch, author=ann, body="note to self @ann")
fan_out_message(m.id)
assert Notification.objects.filter(user=ann).count() == 0
```

### 4. Dedicated email queue
```python
# enqueue onto the "email" queue
send_email.apply_async(args=[subj, body, to], queue="email")
# or set a default route in settings:
CELERY_TASK_ROUTES = {"notifications.tasks.send_email": {"queue": "email"}}
```
```bash
celery -A config worker -Q email -l info     # a worker dedicated to email
```
> Isolating email lets you **scale and fail independently**: a slow SMTP server backs
> up only the `email` queue, not message fan-out; you can give email its own
> concurrency, retries, and even a separate machine, without starving latency-sensitive
> tasks.

### 5. The on_commit race
> `fan_out_message.delay(id)` may be picked up by a worker **microseconds** after you
> enqueue it — possibly *before* the web request's database transaction commits. The
> worker then `Message.objects.get(id=...)` and finds **nothing** (the row isn't
> visible yet), so the notification is silently skipped. Wrapping the enqueue in
> `transaction.on_commit(lambda: fan_out_message.delay(id))` defers it until after the
> commit succeeds, guaranteeing the row exists. (In tests, `CELERY_TASK_ALWAYS_EAGER`
> plus `on_commit` running inside the test transaction sidesteps the broker entirely.)

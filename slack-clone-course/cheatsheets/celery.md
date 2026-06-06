# Cheatsheet — Celery

## Pieces

```
your code ──.delay()──► Redis (broker) ──► worker runs the task
                            ▲
                      Beat enqueues periodic tasks
```

## Define a task

```python
from celery import shared_task

@shared_task
def fan_out(message_id): ...

@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def send_email(self, to, subj, body):
    try: ...
    except Exception as exc: raise self.retry(exc=exc, countdown=2 ** self.request.retries * 10)
```

## Enqueue (don't run inline)

```python
fan_out.delay(msg.id)                       # simplest
send_email.apply_async(args=[...], queue="email", countdown=5)
from django.db import transaction
transaction.on_commit(lambda: fan_out.delay(msg.id))   # avoid the pre-commit race!
```

## Run workers & beat

```bash
celery -A config worker -l info --concurrency 4
celery -A config worker -Q email -l info        # dedicated queue
celery -A config beat -l info                   # scheduler (run exactly ONE)
celery -A config inspect ping                   # liveness
celery -A config inspect active                 # currently-running tasks
```

## Periodic schedule (settings)

```python
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
  "daily-digest": {"task": "notifications.tasks.send_daily_digest",
                   "schedule": crontab(hour=8, minute=0)},
}
```

## Golden rules
- **Pass ids, not objects** — the worker re-fetches fresh, payload stays small.
- **Make tasks idempotent** (`get_or_create`) — workers retry.
- **`transaction.on_commit`** before enqueuing work that reads rows you just wrote.
- **Beat is a singleton** — two beats = double-fired schedules.
- Heavy/slow/external work (email, fan-out, webhooks) belongs in tasks, never in the request.

## Testing

```python
# settings for tests: run inline, no broker
CELERY_TASK_ALWAYS_EAGER = True
```

## Routing to queues (settings)

```python
CELERY_TASK_ROUTES = {"notifications.tasks.send_email": {"queue": "email"}}
```

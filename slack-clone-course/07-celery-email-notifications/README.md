# Module 07 — Celery: Email & Notifications

**Goal:** move slow work — sending email, fanning out notifications — out of the
request/WebSocket path into background workers, with retries and a scheduled digest.

⏱️ ~3 hours · 🎯 Prereq: Module 06. Redis + MailHog running.

> When Ann @-mentions 50 people, you must not make her wait while the server writes
> 50 rows and sends 50 emails. You acknowledge her message instantly and let a
> **worker** do the slow part. That's what Celery is for.

---

## 1. The pieces

```
 web/consumer ──.delay()──► Redis (broker) ──► Celery worker ──► Postgres + SMTP
                                  ▲
                          Celery Beat (scheduler) enqueues periodic tasks
```

- **Broker** — Redis, where queued tasks wait (the same Redis again).
- **Worker** — a separate process that pulls tasks and runs them.
- **Beat** — a scheduler process that enqueues periodic tasks (the daily digest).

`config/celery.py` defines the app; `config/__init__.py` imports it so `@shared_task`
works everywhere; `autodiscover_tasks()` finds each app's `tasks.py`.

## 2. Enqueue vs run

`fan_out_message.delay(message_id)` **enqueues** — it returns immediately, putting a
tiny message (the task name + the id) on Redis. A worker later **runs** it. Notice we
pass an **id, not the object** — the worker re-fetches from the DB, so the payload
stays small and never goes stale.

## 3. Who gets notified (the fan-out)

`fan_out_message` decides recipients by channel kind:

- **DM** → everyone in the conversation except the sender (`kind = dm`).
- **Channel** → only members whose `@username` appears in the body (`kind = mention`).

For each recipient it creates an in-app `Notification` and — *only if they're not
currently online* — sends an email. Active users see the message live; they don't
need an email too.

## 4. Idempotency (because workers retry)

A worker can die mid-task and Celery will re-run it. If `fan_out_message` ran twice,
you'd get duplicate notifications — unless the write is **idempotent**. We use
`get_or_create` keyed on `(user, kind, payload)`, so a re-run is a no-op. *Design
every task to be safe to run more than once.*

## 5. Retries with backoff

`send_email` is decorated `max_retries=3` and calls `self.retry(...)` on failure with
exponential backoff (`10s, 20s, 40s`). A flaky SMTP server or momentary network blip
won't lose the email — it'll be retried, then give up gracefully.

## 6. Scheduled work: the digest

`send_daily_digest` is wired into `CELERY_BEAT_SCHEDULE` to run at 08:00 UTC. Beat
enqueues it; a worker runs it; it emails each user their unread count. We use
`django-celery-beat`'s database scheduler so schedules can also be edited from the
admin without a redeploy.

## 7. How it connects to the rest

Both the WebSocket consumer (`_create_message`) and the REST create path call
`notifications.services.on_new_message(message_id)` after saving — so notifications
fire no matter how a message was posted, and the slow part never blocks the sender.

---

## 8. Do the lab

Run a worker and Beat, post an @mention to an offline user and watch the email land
in MailHog, see notifications appear over the API, and trigger the digest by hand.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

Celery · broker · worker · Celery Beat · idempotent · retry/backoff · fan-out

**Next →** [Module 08: Webhooks & Integrations](../08-webhooks-integrations/)

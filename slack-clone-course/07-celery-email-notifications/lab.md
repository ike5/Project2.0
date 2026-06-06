# Lab 07 — Background Email & Notifications

**You'll:** run a Celery worker and Beat, fire a real @mention that emails an offline
user (landing in MailHog), read notifications over the API, and trigger the digest
manually.

⏱️ ~50 min. Redis + MailHog running (`00-setup/compose.dev.yml`). The web server can
run alongside.

---

## Part A — Start a worker

In a new terminal (venv active, in `apps/slack-backend`):
```bash
celery -A config worker -l info
```
✅ Expected: the worker boots and lists the discovered tasks, including
`notifications.tasks.fan_out_message`, `send_email`, `send_daily_digest`.

In **another** terminal, start the scheduler:
```bash
celery -A config beat -l info
```
✅ Expected: Beat starts and reports the `daily-digest` entry.

---

## Part B — Mention an offline user → email

Make sure **bob** exists and is a member of `#general` but is **not** connected to any
WebSocket (so he counts as offline). As **ann**, post a message that mentions him:

```bash
curl -s -H "Authorization: Bearer $ACCESS" -H 'content-type: application/json' \
  -X POST localhost:8000/api/messages/ \
  -d "{\"channel\":$CH,\"body\":\"hey @bob can you review this?\"}" | jq '.id'
```

Watch the **worker** terminal: you'll see `fan_out_message` run, then `send_email`.

✅ Open MailHog at <http://localhost:8025> — there's an email **to bob** titled
*"New mention in #general"*.

---

## Part C — Read notifications over the API

As **bob**:
```bash
curl -s -H "Authorization: Bearer $BOB" "localhost:8000/api/notifications/?unread=true" | jq
```
✅ Expected: one unread `mention` notification with `payload.message` and `payload.channel`.

Mark it read:
```bash
NID=$(curl -s -H "Authorization: Bearer $BOB" "localhost:8000/api/notifications/?unread=true" | jq '.results[0].id // .[0].id')
curl -s -H "Authorization: Bearer $BOB" -X POST localhost:8000/api/notifications/$NID/read/ | jq
curl -s -H "Authorization: Bearer $BOB" "localhost:8000/api/notifications/?unread=true" | jq 'length // .count'
```
✅ Expected: now zero unread.

---

## Part D — Online users don't get email

Connect **bob** via `wscat` to `#general` (so he's online), then have ann mention him
again. Watch the worker: a notification is still created, but **no `send_email`** runs
— we don't email active users. Confirm MailHog gets no new mail.

✅ **Checkpoint:** email is gated on presence (`is_online`).

---

## Part E — Retries and the digest

Stop MailHog (`docker compose -f ../00-setup/compose.dev.yml stop mailhog`) and post
another mention. Watch `send_email` **retry** with backoff in the worker log, then
give up after 3 tries (no crash). Start MailHog again.

Trigger the digest by hand instead of waiting for 08:00:
```bash
python manage.py shell -c "from notifications.tasks import send_daily_digest; send_daily_digest.delay()"
```
✅ Expected: the worker runs it; users with unread notifications get a digest email in MailHog.

---

## What you learned
- `.delay()` enqueues work to Redis; a separate worker runs it off the request path.
- Notifications fan out by channel kind; email is gated on whether the user is online.
- Tasks are idempotent (`get_or_create`) and email retries with backoff.
- Beat schedules periodic work like the daily digest.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 08](../08-webhooks-integrations/).

# Lab 02 — Boot the Backend on Postgres

**You'll:** set up a virtualenv, configure the backend, run migrations against your
dev Postgres, create an admin user, and verify the API health check and ORM
relationships all work.

⏱️ ~50 min. Run from `slack-clone-course/apps/slack-backend`. The dev data services
([`00-setup/compose.dev.yml`](../00-setup/compose.dev.yml)) must be up.

---

## Part A — Environment & dependencies

```bash
cd apps/slack-backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # points at localhost Postgres/Redis from Module 00
```

✅ **Checkpoint:** `pip list` shows Django 5, DRF, channels, celery, etc.

> The provided code already contains the finished models. The point of this lab is
> to make it *run on your machine* and understand each step.

---

## Part B — Inspect what the project checks find

```bash
python manage.py check
```
✅ Expected: `System check identified no issues (0 silenced).`

This loads every app and setting without touching the database — a fast way to
catch typos before migrating.

---

## Part C — Create and apply migrations

```bash
python manage.py makemigrations
```
✅ Expected: initial migrations for `accounts`, `workspaces`, `chat`,
`notifications`, `webhooks`:
```
Migrations for 'accounts':
  accounts/migrations/0001_initial.py
    - Create model User
...
```

Apply them to Postgres:
```bash
python manage.py migrate
```
✅ Expected: a long list ending in `... OK`, including Django's own auth/admin
tables and our app tables.

Peek at the real tables in Postgres:
```bash
docker compose -f ../../00-setup/compose.dev.yml exec postgres \
  psql -U slack -d slack -c '\dt'
```
You'll see `accounts_user`, `workspaces_workspace`, `chat_channel`, `chat_message`, …

✅ **Checkpoint:** your hand-drawn ERD from Module 01 now exists as real tables.

---

## Part D — Run the server and hit the health check

```bash
python manage.py runserver
```
In another terminal:
```bash
curl -s localhost:8000/api/health/ ; echo
# {"status": "ok"}
```
✅ This `/api/health/` endpoint is what Docker and Kubernetes will probe later.

---

## Part E — Create a superuser and explore the admin

```bash
python manage.py createsuperuser    # enter email, username, password
```
Open <http://localhost:8000/admin/> and log in. Create a **Workspace**, add yourself
as a **Membership** (role `owner`), and create a `#general` **Channel**.

✅ **Checkpoint:** you created real rows through the admin with no frontend yet.

---

## Part F — Prove the relationships from the shell

```bash
python manage.py shell
```
```python
from accounts.models import User
from workspaces.models import Workspace, Membership
from chat.models import Channel, Message

u = User.objects.get(username="<your-username>")
w = Workspace.objects.first()
ch = Channel.objects.get(name="general")

# post a message
Message.objects.create(channel=ch, author=u, body="Hello from the shell!")

# the relationships you designed in Module 01:
list(u.workspaces.values_list("slug", flat=True))   # ['your-workspace']
ch.messages.count()                                  # 1
w.channels.count()                                   # 1
```
✅ **Checkpoint:** `u.workspaces` and `ch.messages` traverse the `Membership` and
`Message` relations exactly as designed.

---

## What you learned
- 12-factor settings load config from env, so one codebase runs everywhere.
- A custom email-based `User` must be set before the first migration.
- The Module 01 ERD became Django models, migrations, and real Postgres tables.
- The admin is a free back office; the ORM traverses your relationships in Python.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 03](../03-auth-simplejwt/).

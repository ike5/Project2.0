# Module 02 — Django + Postgres Foundations

**Goal:** stand up the Django backend with 12-factor settings, a custom user model,
and the core data model (workspaces, channels, messages) backed by Postgres.

⏱️ ~2.5 hours · 🎯 Prereq: Modules 00–01. Dev data services running.

> This is the spine of the whole backend. We make two decisions now that are very
> hard to change later — a **custom User model** and the **schema** — so we do them
> carefully and on purpose.

---

## 1. Project layout

The backend lives in [`apps/slack-backend/`](../apps/slack-backend/). It's a
standard Django project with a `config` package and one app per bounded context:

```
slack-backend/
├── config/         settings, urls, asgi, wsgi  (+ celery later)
├── accounts/       custom User
├── workspaces/     Workspace, Membership, Invite
├── chat/           Channel, ChannelMember, Message, Reaction, Attachment
├── notifications/  Notification (filled in Module 07)
├── webhooks/       Incoming/Outgoing webhooks (filled in Module 08)
├── manage.py
└── requirements.txt
```

> The full app already exists in `apps/` as the finished reference. Read it as you
> go; when building from scratch you'd add each app in the module that introduces it.

## 2. 12-factor settings

`config/settings.py` reads everything environment-specific from env vars via
**django-environ** — `SECRET_KEY`, `DEBUG`, `DATABASE_URL`, `REDIS_URL`, email,
storage. The *same code* then runs in dev, CI, and the Kubernetes cluster; only the
env changes. In dev we load a local `.env`; in containers, real env vars win.

```python
DATABASES = {"default": env.db("DATABASE_URL", default="postgres://slack:slack@localhost:5432/slack")}
```

## 3. Why a custom User — and why now

We log in with **email**, not a username (like Slack). Django's default user is
username-first, so we define our own `accounts.User` (email is the `USERNAME_FIELD`;
`username` becomes the @-mention handle). 

> **The rule:** set `AUTH_USER_MODEL` *before your first migration*. Changing it
> after tables exist means a brutal manual migration. That's why Module 02, not
> later, owns this.

## 4. The schema in Django models

Module 01's ERD becomes Django models. A few choices worth noticing:

- **`Membership`** is an explicit `through` model on a `ManyToMany` so it can carry
  a `role` and a uniqueness constraint (one membership per user per workspace).
- **`Channel.name` is nullable** because **DMs are channels** with no name.
- **`Message.parent`** is a self-FK → threads. The model declares an index on
  `(channel, -id)` because "this channel's latest messages" is the hottest query.
- **`ChannelMember.last_read_message_id`** is the seed of unread counts (Module 06).
- **Constraints live in the database** (`UniqueConstraint`) — integrity you can't
  accidentally bypass from app code.

## 5. Migrations: your schema's version control

`makemigrations` turns model changes into migration files; `migrate` applies them.
Migrations are **committed to git** — they're the reproducible history of your
schema, replayed identically in every environment (including the K8s migration Job
in Module 13).

## 6. The admin: a free back office

Registering models with `django.contrib.admin` gives you a working CRUD UI at
`/admin/` — perfect for inspecting data while you build, before any frontend exists.

---

## 7. Do the lab

Install the backend, point it at Postgres, run the migrations, create a superuser,
hit the health endpoint, and prove the models + relationships work from the Django shell.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

Django · ORM · migration · 12-factor config · custom user · through model · constraint

**Next →** [Module 03: Auth with SimpleJWT](../03-auth-simplejwt/)

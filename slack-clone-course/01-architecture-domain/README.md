# Module 01 — Architecture & Domain Model

**Goal:** understand *what* you're building before you build it — the product
concepts, the data model behind them, and how requests and real-time events flow
through the system.

⏱️ ~1.5 hours · 🎯 Prereq: Module 00 complete (data services running).

> A chat app looks simple and isn't. Getting the domain model right now — how
> workspaces, channels, memberships, and messages relate — saves you from painful
> migrations later. We'll design it on purpose.

---

## 1. The product, in one paragraph

A user signs up and joins (or creates) a **workspace** — an organization's private
space. Inside a workspace are **channels** (public or private topic rooms) and
**direct messages** (DMs between a few people). Users post **messages**; messages
can start **threads** (replies), carry **reactions** (emoji), **mention** people
(`@ann`), and include **file attachments**. The app shows who's **online**
(presence), keeps **unread** counts, and sends **notifications** (in-app + email)
when you're mentioned or DM'd while away.

## 2. The core entities

| Entity | What it represents | Key relationships |
|--------|--------------------|-------------------|
| **User** | A person's account | belongs to many workspaces (via Membership) |
| **Workspace** | An org's private space | has many channels and members |
| **Membership** | A user's seat in a workspace | links User ↔ Workspace, carries role (owner/admin/member) |
| **Channel** | A room within a workspace | has many messages; public or private; DMs are channels too |
| **ChannelMember** | Who's in a (private/DM) channel | links User ↔ Channel |
| **Message** | A posted message | belongs to a channel + author; may have a parent (thread) |
| **Reaction** | An emoji on a message | links User ↔ Message + emoji |
| **Attachment** | A file on a message | belongs to a message; points at object storage |

> **Design choice: DMs are channels.** Instead of a separate "conversation" type, a
> DM is just a channel with `kind="dm"` and no name. This keeps messaging code
> uniform — one consumer, one message table, one read path.

## 3. The data model (ERD)

```
 User ───< Membership >─── Workspace
   │                          │
   │                          └──< Channel >── ChannelMember >── User
   │                                  │
   └────────< Message >───────────────┘
                │  │ │
     parent ────┘  │ └──< Attachment
   (thread reply)  │
                   └──< Reaction >── User
```
- `>──` / `──<` mark the "many" side. A Message has one author (User) and one
  Channel; a Channel has many Messages.
- `parent` is a self-reference on Message: a reply points at the message it answers
  (a thread is a message plus its children).

## 4. Two request paths: REST vs WebSocket

The backend speaks two protocols, on purpose:

```
Action                         Path           Why
─────────────────────────────  ─────────────  ─────────────────────────────
Login, list channels, history  REST (DRF)     request/response, cacheable, paginated
Send/receive a live message    WebSocket      push to everyone instantly, both ways
Typing… / presence             WebSocket      ephemeral, high-frequency, not stored as REST
Upload a file                  REST + S3      get a presigned URL, upload direct to storage
```

You **load** a channel's history over REST, then **subscribe** to new messages over
a WebSocket. New posts are written to Postgres *and* broadcast over the Redis
channel layer to every connected client.

## 5. How a message travels (the whole stack in one trace)

```
1. Browser sends {type:"message.new", text:"hi"} over its WebSocket
2. Django consumer authenticates the socket (JWT), validates membership
3. Consumer writes the Message row to Postgres
4. Consumer broadcasts to the channel's GROUP via the Redis channel layer
5. Every server holding a socket for that channel receives the broadcast…
6. …and pushes it down each WebSocket to the browsers → message appears instantly
7. In parallel: a Celery task fans out notifications (email if a mentioned user is away)
```

Every numbered step is a module: 03 (auth), 02/04 (models + REST), 05 (consumer +
channel layer), 06 (presence), 07 (Celery notifications).

## 6. Why this needs the heavy machinery

- **Redis as channel layer** — with multiple backend Pods (Module 15), a message
  received by Pod A must reach a socket held by Pod B. Redis is the shared bus.
- **Celery** — sending email or fanning out 500 notifications must not block the
  request. Push it to a worker.
- **Operators / HA** — chat is "always on." Losing the database for 30 seconds is
  very visible, so Module 14–15 make Postgres and Redis fail over automatically.

---

## 7. Do the lab

Make the model concrete: load a seed schema into your dev Postgres and answer real
product questions ("which channels is ann in?", "what are the unread messages?")
with SQL — so the relationships stick before you rebuild them in Django.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

workspace · channel · membership · thread · presence · channel layer · WebSocket · REST

**Next →** [Module 02: Django + Postgres Foundations](../02-django-postgres/)

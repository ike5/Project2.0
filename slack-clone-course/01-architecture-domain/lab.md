# Lab 01 — Make the Domain Model Concrete

**You'll:** load a hand-written exploration schema into Postgres and answer real
product questions with SQL — so the entity relationships are intuitive *before* you
rebuild them as Django models next module.

⏱️ ~40 min. Run from `slack-clone-course/01-architecture-domain`. The dev data
services from Module 00 must be up.

> This schema is a **throwaway**. We write SQL by hand here purely to learn the
> shape of the data. Module 02 replaces it with proper Django models + migrations.

---

## Part A — Load the seed schema

```bash
docker compose -f ../00-setup/compose.dev.yml exec -T postgres \
  psql -U slack -d slack < code/seed.sql
```

✅ Expected: a stream of `CREATE TABLE` / `INSERT` lines, no errors. The data lives
in a separate `explore` schema so it won't collide with Django later.

Open a session to query it:
```bash
docker compose -f ../00-setup/compose.dev.yml exec postgres \
  psql -U slack -d slack -c 'SET search_path TO explore;' -c '\dt explore.*'
```
…or interactively (recommended for the rest of the lab):
```bash
docker compose -f ../00-setup/compose.dev.yml exec postgres psql -U slack -d slack
```
```sql
SET search_path TO explore;     -- run this first each session
```

---

## Part B — Answer product questions with joins

**"Which workspaces is ann a member of, and what's her role?"**
```sql
SELECT w.name, m.role
FROM membership m
JOIN app_user u  ON u.id = m.user_id
JOIN workspace w ON w.id = m.workspace_id
WHERE u.username = 'ann';
```
✅ Expected: `Acme | owner`.

**"What public channels exist in Acme?"**
```sql
SELECT name FROM channel
WHERE workspace_id = 1 AND kind = 'public';
```
✅ Expected: `general`, `random`.

**"Show #general's messages with author names, oldest first."**
```sql
SELECT u.username, msg.body
FROM message msg
JOIN app_user u ON u.id = msg.author_id
WHERE msg.channel_id = 1
ORDER BY msg.id;
```
✅ **Checkpoint:** you see the welcome message, bob's hi, and cat's reply.

---

## Part C — Threads (the self-join)

A thread is a message plus the messages whose `parent_id` points at it.

```sql
-- the reply and what it replies to
SELECT child.body AS reply, parent.body AS replying_to
FROM message child
JOIN message parent ON parent.id = child.parent_id
WHERE child.parent_id IS NOT NULL;
```
✅ Expected: `hey bob, glad you joined` → replying to `Hi everyone`.

---

## Part D — Unread counts (the feature behind the red badge)

Each `channel_member` row stores `last_read` (the id of the last message that user
has seen). Unread = messages in the channel newer than that.

```sql
-- how many unread messages does each member of the DM (channel 4) have?
SELECT u.username,
       COUNT(m.id) AS unread
FROM channel_member cm
JOIN app_user u ON u.id = cm.user_id
LEFT JOIN message m
       ON m.channel_id = cm.channel_id
      AND m.id > cm.last_read
WHERE cm.channel_id = 4
GROUP BY u.username;
```
✅ Expected: ann read up to msg 2 → some unread; bob read up to msg 1 → more
unread. This exact query becomes a cached counter in Module 06.

---

## What you learned
- The eight core entities and how they join (User ↔ Membership ↔ Workspace ↔ Channel ↔ Message).
- DMs are just channels (`kind='dm'`) — messaging stays uniform.
- Threads are a self-reference on `message.parent_id`.
- Unread counts come from comparing message ids to a per-member `last_read`.

Clean up the scratch schema (Module 02 starts fresh):
```sql
DROP SCHEMA explore CASCADE;
```

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 02](../02-django-postgres/).

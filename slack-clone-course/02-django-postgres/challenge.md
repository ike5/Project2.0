# Challenge 02 — Extend the Model

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Add a field.** Give `Channel` a boolean `is_archived` (default `False`).
   Generate and apply the migration. Confirm the column exists in Postgres.

2. **Pin the model.** A workspace owner should be able to *pin* a message. Add a
   `pinned` boolean to `Message` with a sensible default, migrate, and pin one
   message from the shell.

3. **Query like a feature.** Without writing SQL, use the ORM to fetch the **5 most
   recent** messages in `#general`, newest first, with the author's username in the
   same query (avoid N+1 — hint: `select_related`).

4. **Enforce a rule in the database.** A user shouldn't be able to react to the same
   message with the same emoji twice. Confirm the existing `uniq_reaction`
   constraint by trying to create a duplicate `Reaction` in the shell and observing
   the `IntegrityError`.

5. **Stretch:** Explain in two sentences why `Membership` is an explicit `through`
   model instead of a plain `ManyToManyField` between `User` and `Workspace`.

## Success criteria
- [ ] `chat_channel` has an `is_archived` column via a committed migration.
- [ ] `Message.pinned` exists and you pinned one from the shell.
- [ ] You fetched the latest 5 messages with authors in a single optimized query.
- [ ] A duplicate reaction raises `IntegrityError` (the DB constraint works).
- [ ] You can justify the `through` model.

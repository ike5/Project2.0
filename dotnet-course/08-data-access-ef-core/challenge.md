# Challenge 08 — Model & Query

Solution in [`solutions/`](./solutions/). Try first.

## Tasks
1. **A related entity.** Add a `Tag` entity and a many-to-? relationship so a
   `TaskItem` can have multiple tags (one-to-many `TaskItem → Tags` is fine). Create
   a migration and apply it. Use `Include()` to return tasks with their tags.

2. **Server-side filtering.** Add `GET /api/tasks?done=true&search=foo` that filters
   by completion and title substring **in SQL** (the `Where` runs before
   materialization). Confirm via EF's SQL logging that filtering isn't done in memory.

3. **Translation trap.** Write a query that throws "could not be translated" (e.g.
   calling a custom C# method inside `Where` over the `DbSet`), then fix it by
   materializing first or rewriting the predicate. Explain the cause.

4. **Migration discipline (short answer).** You need to rename a column. Why must you
   create a *new* migration rather than editing the last applied one? What does
   `dotnet ef migrations remove` do (and when is it safe)?

## Success criteria
- [ ] Tags relationship exists, migrated, and returned via `Include`.
- [ ] The filter runs in SQL (verified in the logged query), not in memory.
- [ ] You reproduced and fixed a translation error and can explain it.
- [ ] Correct reasoning on migration immutability + when `remove` is safe.

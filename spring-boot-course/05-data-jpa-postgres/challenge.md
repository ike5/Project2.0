# Challenge 05 — Schema, Queries, and the Repository

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **New column.** Add a `priority` column to `task` (values `low`,
   `medium`, `high`). Write a `V2__add_task_priority.sql` migration. Default
   to `medium`. Add a `priority` field to the entity and a DTO field to
   `TaskResponse`. Add a `setPriority(String)` method. Restart and confirm
   the migration applied (`select * from flyway_schema_history;` in psql).

2. **A derived query.** Add a repository method
   `List<Task> findByDoneAndPriority(boolean done, String priority)` — Spring
   derives it from the name. Test it via the service.

3. **A custom JPQL query.** Add `@Query("SELECT t FROM Task t WHERE ... ORDER BY
   t.createdAt DESC")` returning the 10 most recent open tasks. Map it to
   `GET /api/tasks/recent` in the controller.

4. **An audit field.** Add `updated_at` to the entity with
   `@LastModifiedDate` and enable JPA auditing. Touch a row via `PUT` and
   confirm `updated_at` is later than `created_at` (in psql).

5. **A unique constraint.** Add `email` to a new `app_user` table. Make it
   unique. Create a `V3__create_app_user.sql` migration. Try to insert two
   rows with the same email from psql and observe the error.

6. **Stretch:** Add a `TaskSpecifications` class using
   `JpaSpecificationExecutor` so the `GET /api/tasks?done=true&priority=high`
   endpoint filters by an arbitrary combination of fields. This is the
   "specification" pattern — a fluent builder for dynamic queries.

## Success criteria

- [ ] `priority` column exists via a Flyway migration; the entity, DTO, and
  controller all reflect it.
- [ ] `findByDoneAndPriority` works and is exercised by curl.
- [ ] `GET /api/tasks/recent` returns the 10 newest open tasks.
- [ ] `updated_at` advances on update; auditing is enabled.
- [ ] A duplicate `email` insert fails with a constraint violation.
- [ ] Stretch: a dynamic filter endpoint works.

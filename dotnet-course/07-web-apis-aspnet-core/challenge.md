# Challenge 07 — Round Out the API

Solution in [`solutions/`](./solutions/). Try first.

## Tasks
1. **DELETE + filtering.** Add `DELETE /api/tasks/{id}` (204/404) and
   `GET /api/tasks?done=true` that filters by completion using a query-string bound
   `bool? done` parameter.

2. **Port to a controller.** Reimplement the `GET` and `POST` endpoints as a
   `[ApiController]`-based `TasksController` (constructor-injected `ITaskService`,
   `[HttpGet]`/`[HttpPost]`, `Ok`/`CreatedAtAction`/`BadRequest`). Register controllers
   with `builder.Services.AddControllers()` + `app.MapControllers()`.

3. **Lifetime bug.** Change the service registration from `AddSingleton` to
   `AddScoped` and observe what happens to the in-memory list across requests. Explain
   why (and why a real app uses `Scoped` + a database instead).

4. **Validation filter (stretch).** Add a minimal-API endpoint filter that rejects any
   request whose `Title` exceeds 50 chars with a `400`, without putting the check in
   the handler.

## Success criteria
- [ ] DELETE works (204/404) and the `?done=` filter returns the right subset.
- [ ] A controller-based version of GET/POST behaves identically to the minimal API.
- [ ] You can explain why `Scoped` "loses" the in-memory list between requests.
- [ ] (Stretch) The endpoint filter enforces the title length centrally.

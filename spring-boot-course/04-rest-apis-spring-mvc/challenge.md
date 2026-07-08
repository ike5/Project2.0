# Challenge 04 — The API Contract

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Filter by `done`.** Add `GET /api/tasks?done=true` that returns only
   completed tasks. Use `@RequestParam(defaultValue = "false") boolean done`
   in the controller. Update `TaskService` to support the filter (the
   in-memory repo already has all the data — just filter in the service).

2. **A "complete" endpoint.** `POST /api/tasks/{id}/done` — shortcut for
   marking a task done. Returns `200` with the updated task. Add it to
   `TaskService` as `complete(id)`.

3. **Bulk create.** `POST /api/tasks/bulk` that accepts a JSON array of
   `CreateTaskRequest` and returns the created `TaskResponse`s. Use
   `@RequestBody List<@Valid CreateTaskRequest>`.

4. **Search by title fragment.** `GET /api/tasks/search?q=milk` — case-
   insensitive substring search. Return an empty list (not 404) when no
   match.

5. **Custom header.** Make every response carry an `X-App-Name: taskforge`
   header. Either set it per controller method with `ResponseEntity`, or
   add a `HandlerInterceptor` and register it in a `WebMvcConfigurer`.
   (Hint: look up `HandlerInterceptor.preHandle`.)

6. **Stretch:** Add a `@ControllerAdvice` that catches
   `MethodArgumentNotValidException` and returns a `400` with a body like
   `{"errors": ["title: must not be blank"]}`. (Module 06 covers this in
   depth — here's a sneak peek.)

## Success criteria

- [ ] `GET /api/tasks?done=true` filters.
- [ ] `POST /api/tasks/{id}/done` completes a task.
- [ ] `POST /api/tasks/bulk` accepts an array.
- [ ] `GET /api/tasks/search?q=...` returns matches.
- [ ] Every response carries `X-App-Name: taskforge`.
- [ ] Stretch: a `@ControllerAdvice` returns 400 with field errors.

# Challenge 06 — The Error Contract

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **A custom validation annotation.** Write `@NoHtml` that rejects strings
   containing `<` or `>`. Apply it to `description` in `CreateTaskRequest`
   and `UpdateTaskRequest`. Confirm `POST` with `<script>` is rejected.

2. **Cross-field validation in the service.** Add a `Task` rule: a task with
   `done = true` cannot be reopened (i.e. you cannot `PUT` it with
   `done = false`). Throw a `ConflictException` in the service.

3. **A `BadCredentialsException` handler (preview).** Even though auth comes
   in Module 07, add a handler now that returns `401` with a problem
   detail. (You'll wire it to Spring Security next module.)

4. **Pagination validation.** `GET /api/tasks?page=0&size=20` — validate that
   `size` is between 1 and `TaskforgeProperties.maxPageSize()` (from
   Module 03). Reject with 400 otherwise. The trick: use
   `@Validated` on the controller class plus `@Min` / `@Max` on the
   `@RequestParam`.

5. **Localized messages.** Add a `ValidationMessages.properties` file and
   use `{custom.title.required}` in the `@NotBlank` message. Confirm the
   resolved text appears in the response. (Spring Boot picks up the file
   automatically.)

6. **Stretch:** Add a request-id filter (`OncePerRequestFilter`) that puts
   a `traceId` on the MDC and echoes it as `X-Trace-Id` on every response —
   so support engineers can correlate client reports with server logs.
   (You'll re-use this in Module 09.)

## Success criteria

- [ ] `@NoHtml` rejects `<` and `>` in description.
- [ ] Cannot reopen a completed task; `ConflictException` returns 409.
- [ ] A `BadCredentialsException` handler returns 401 with a problem detail.
- [ ] Pagination `size` outside `[1, max]` is rejected with 400.
- [ ] A localized message resolves from `ValidationMessages.properties`.
- [ ] Stretch: `X-Trace-Id` is on every response.

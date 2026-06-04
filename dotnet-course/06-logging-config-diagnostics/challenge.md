# Challenge 06 — Make It Observable & Configurable

Solution in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Structured over interpolated.** Find any log call using string interpolation and
   convert it to a message template with named fields. Explain (one sentence) why the
   template version is better for support.

2. **Correlation id.** Add middleware that reads or generates an `X-Correlation-ID`
   header and pushes it into the Serilog `LogContext` so every log line for that
   request carries it. Verify two requests show different ids.

3. **Typed Options with validation.** Extend `ApiOptions` with `MaxTitleLength` and
   validate it's between 1 and 500 at startup using `ValidateDataAnnotations()` +
   `ValidateOnStart()`. Prove the app refuses to start with an invalid value.

4. **Env-specific behavior.** Make the API return detailed error responses in
   Development but generic ones in Production (hint: `app.Environment.IsDevelopment()`
   or `UseExceptionHandler`).

## Success criteria
- [ ] A converted structured log line with named fields; rationale stated.
- [ ] Correlation id appears on all logs for a request and differs across requests.
- [ ] Invalid `MaxTitleLength` fails fast at startup with a clear message.
- [ ] Error detail differs between Development and Production.

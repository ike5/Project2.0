# Challenge 09 — Logs, Profiles, and Config

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **MDC for the authenticated user.** Add the user id and email to the
   MDC inside the JWT filter (after you set the `Authentication`). Every
   log line should now show `[user=42 ann@example.com]`. Update
   `logback-spring.xml` to print the `user` MDC key.

2. **Conditional bean for email.** Make `EmailSender` a
   `@ConditionalOnProperty(name = "taskforge.email.enabled", havingValue = "true")`
   bean. In dev (`enabled: false`) the bean doesn't exist; in prod it does.
   Inject a `MockEmailSender` for tests via `@MockBean` or a test config.

3. **Fail fast on a missing secret.** Set `taskforge.security.jwt.secret`
   to an empty string in `application.yml`. Start the app and confirm
   Spring refuses to start with a clear error pointing at the missing
   property. Restore the secret after.

4. **Multiple profiles.** Add `application-ci.yml` that uses an in-memory
   H2 (or another testcontainer) and `taskforge.email.enabled=false`.
   Activate with `SPRING_PROFILES_ACTIVE=ci` and confirm `GET /actuator/health`
   works without the dev Postgres.

5. **Custom property source.** Load a config value from a file:
   `@PropertySource(value = "classpath:branding.yml", factory = YamlPropertySourceFactory.class)`.
   (Spring's `YamlPropertySourceFactory` is in the docs but you may need
   to write a 5-line factory if you don't use `spring-boot-starter`.)

6. **Stretch:** Wire Micrometer's `@Observed` to wrap the `TaskService`
   methods. Every call shows up in a `task.create` timer with
   `outcome=success` / `outcome=error`. Confirm in
   `/actuator/metrics/task.create`. (Module 15 builds on this.)

## Success criteria

- [ ] Log lines include the user id/email from the JWT.
- [ ] `EmailSender` is conditional on `taskforge.email.enabled`.
- [ ] A missing `jwt.secret` fails startup loudly.
- [ ] The `ci` profile starts without the dev Postgres.
- [ ] A custom property source loads a value.
- [ ] Stretch: a Micrometer timer is exposed on `/actuator/metrics`.

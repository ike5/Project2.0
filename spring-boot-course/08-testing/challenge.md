# Challenge 08 — A Test Suite You Can Trust

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Test the security rules.** Add a slice test where user 42 tries to
   `PUT /api/tasks/1` (owned by user 99). Assert the response is `403` and
   the body has `type: ".../forbidden"`. Use `.with(jwt().jwt(j -> j.subject("42")))`.

2. **Test the validation handler.** A `POST` with `{"title":""}` returns
   `400` with a `ProblemDetail`. Assert the response has
   `$.errors[0].field == "title"` and `$.type` contains `"validation"`.

3. **Test the repository with constraints.** In a Testcontainer test, try
   to insert two `app_user` rows with the same `email`. Assert the second
   insert throws `DataIntegrityViolationException`.

4. **Parametrized tests.** Convert one of your service tests into a
   `@ParameterizedTest` with `@CsvSource` to cover multiple inputs:
   `("","missing title")`, `("a","ok")`, `("   ","missing title")`.

5. **Testcontainers for Redis + Kafka.** Add a small test that boots a
   Redis container and a Kafka container, and verify that
   `RedisTemplate.opsForValue().set("k","v")` round-trips, and that
   `KafkaTemplate.send(...)` lands in a topic consumed by a
   `@KafkaListener`. (This previews Modules 10 and 11.)

6. **Stretch:** Add **contract tests** with Spring Cloud Contract — record
   a request/response pair, generate a stub, and verify the consumer side.
   This is how large orgs prevent API breakage between teams.

## Success criteria

- [ ] Cross-user edit returns 403 in a slice test.
- [ ] Validation handler returns the right problem detail.
- [ ] Duplicate-email insert is blocked at the DB level (real constraint).
- [ ] A `@ParameterizedTest` runs multiple cases.
- [ ] Testcontainers exercise Redis and Kafka in tests.
- [ ] Stretch: a contract test exists (optional).

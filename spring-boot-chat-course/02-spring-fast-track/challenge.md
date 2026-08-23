# Challenge 02 — Make Spring Tell You the Truth

Solutions in [`solutions/`](./solutions/). Try first.

Every task here is about *seeing* what Spring is doing, rather than trusting it.
That habit is what separates the two hours you'll spend debugging Module 06 from
the two days.

## Tasks

1. **Override an auto-configured bean, and prove you did.**
   Define your own `RedisTemplate<String, String>` bean that uses
   `StringRedisSerializer` for keys and `GenericJackson2JsonRedisSerializer` for
   values. Then show, via `/actuator/conditions`, that Spring Boot's default
   `redisTemplate` is **no longer** registered — quote the condition message that
   changed.

   Then explain in two sentences why the default `RedisTemplate` uses JDK
   serialization, and why that would be a bad choice for Pulse. (Hint: run
   `redis-cli GET` on a key written with each serializer and compare.)

2. **Wire the `SessionRegistry` from Module 01 into Spring.**
   Register your `ConcurrentSessionRegistry` as a bean and expose a
   `/rooms/{id}/sessions` REST endpoint returning its members. Then write a
   `@SpringBootTest` proving the bean is a **singleton** — the same instance is
   injected into two different collaborators.

   Then deliberately add a mutable `int` field to it, hit the endpoint from 100
   concurrent virtual threads, and show the field is wrong. Fix it. This is the
   singleton-mutability trap from the README, made concrete.

3. **Add a custom health indicator that can fail.**
   Write a `HealthIndicator` named `fanoutBacklog` that reports `DOWN` when a
   simulated backlog counter exceeds a configurable threshold. Wire it so it
   appears in `/actuator/health` **and** affects `/actuator/health/readiness` —
   but **not** `/actuator/health/liveness`.

   Then answer in writing: why must a backlog indicator never affect liveness?
   Describe the specific failure cascade that would result if it did.

4. **Add explicit admission control.**
   Using Module 01's lesson, add a `Semaphore`-based limit around a simulated
   database call so that at most 50 requests are in flight at once, and requests
   beyond that queue for at most 2 seconds before returning `503` with a
   `Retry-After` header.

   Prove it with a load test: fire 500 concurrent requests and show the p99
   latency with and without admission control, plus the number of 503s.

5. **Profiles.**
   Create `application-bench.yml` that raises the Hikari pool to 50, sets
   logging to `WARN`, and disables `open-in-view`. Show the app picking it up
   both via `--spring.profiles.active=bench` and via `SPRING_PROFILES_ACTIVE`.
   Confirm with `/actuator/configprops` that the value actually changed.

6. **Stretch — measure startup and find the slow part.**
   Add `spring-boot-starter-aot` and compare startup time before and after. Then
   use `-Dspring.context.startup=true` plus the `startup` Actuator endpoint to
   find the three slowest beans to initialize. Report them.

## Success criteria

- [ ] A custom `RedisTemplate` replaces the auto-configured one, proven via
      `/actuator/conditions`, with the serializer difference shown in `redis-cli`
- [ ] `SessionRegistry` is a Spring bean; a test proves singleton scope
- [ ] The mutable-field race is demonstrated and then fixed
- [ ] `fanoutBacklog` affects readiness but not liveness, with the cascade
      explained
- [ ] Admission control returns 503 + `Retry-After` under overload, with p99
      measured both ways
- [ ] The `bench` profile is proven active via `/actuator/configprops`
- [ ] Stretch: the three slowest beans are named with timings

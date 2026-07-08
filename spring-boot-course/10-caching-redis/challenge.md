# Challenge 10 — Caching the Right Things

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Cache the user task list.** Add `@Cacheable("userTasks", key="#ownerId")`
   to a service method `listOpenForUser(Long ownerId)`. Evict on every
   `create`/`update`/`delete` with `@CacheEvict(value = "userTasks", allEntries = true)`.

2. **Programmatic Redis.** Add a `LoginAttemptService` that uses
   `RedisTemplate` to count failed logins for an IP in a 5-minute window.
   Reject (429) after 5 attempts. Inject it into the auth flow.

3. **`@CachePut` on update.** Replace `@CacheEvict` on `update(...)` with
   `@CachePut` so the cache is updated **with the new value** rather than
   evicted. Verify the cache is fresh after a PUT (no DB read on the next
   GET).

4. **Multi-region TTLs.** Configure different TTLs for different caches:
   `tasks: 5m`, `userTasks: 30s`, `authFailures: 5m`. Use
   `RedisCacheManagerBuilderCustomizer.withInitialCacheConfigurations(...)`.

5. **A two-level cache.** Add Caffeine as an in-process L1 in front of
   Redis. Confirm: first read is "DB then both caches"; second read is L1
   hit; reads from a *different* instance hit L2 (Redis) but skip L1.

6. **Stretch:** Implement a `CacheMetricsBinder` (or use
   `MeterBinder` for `CacheStatistics`) so `/actuator/metrics/cache.gets`
   and `cache.puts` are visible. (Module 15 builds on this for Prometheus.)

## Success criteria

- [ ] The user task list is cached per user and evicted on writes.
- [ ] Login throttling blocks an IP after 5 failed attempts in 5 minutes.
- [ ] `@CachePut` keeps the cache fresh after `update`.
- [ ] Different caches have different TTLs.
- [ ] L1 + L2 cache is wired; different instances share L2.
- [ ] Stretch: cache metrics are exposed.

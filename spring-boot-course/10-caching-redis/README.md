# Module 10 — Caching with Redis & Spring Cache

**Goal:** put a **Redis cache** in front of the database so that the second
read of a task is microseconds, not milliseconds. You'll learn the Spring
Cache abstraction (`@Cacheable`, `@CacheEvict`, `@CachePut`), the **cache
aside** pattern, and how to keep your cache **correct** when data changes.

⏱️ ~2 hours · 🎯 Prereq: Modules 02–09 complete (working tested secure app).

> Caching is one of the cheapest performance wins you can apply. The hard
> part isn't turning it on — it's keeping the cache **consistent** with the
> source of truth.

---

## 1. The problem — read amplification

```
GET /api/tasks/1
   │
   ▼
TaskController.get(1)        ~0.1 ms
   ▼
TaskService.get(1)           ~0.1 ms
   ▼
TaskRepository.findById(1)   ~1–5 ms   ← DB roundtrip
   ▼
Hibernate ORM                ~0.5 ms
   ▼
HikariCP get connection      ~0.5 ms
   ▼
Postgres SELECT              ~0.5 ms   ← network + disk
   ▼
Hibernate map row            ~0.1 ms
   ▼
HTTP response                ~0.1 ms
```
**Total: 3–7 ms** for a single read of one row by primary key.

If 90% of those reads are repeats (the common case for a backend), a Redis
cache drops the inner four steps to **~0.2 ms** — a 15× speedup.

---

## 2. Cache-aside — the pattern you'll use

```
GET /api/tasks/1
   │
   ▼
1. Look in Redis       (key: "task:1")
   hit  → return       ~0.1 ms
   miss ↓
2. Look in Postgres    ~3 ms
3. Write to Redis      ~0.5 ms (TTL = 5 min)
4. Return
```

```
PUT /api/tasks/1
   │
   ▼
1. Update Postgres
2. Delete key "task:1" from Redis
3. Return
```

The pattern is called **cache-aside**: the app manages the cache. Spring's
`@Cacheable` + `@CacheEvict` implement it for you.

---

## 3. Add the dependencies

`pom.xml`:
```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-cache</artifactId>
</dependency>
```

`application.yml`:
```yaml
spring:
  data:
    redis:
      host: localhost
      port: 6379
      timeout: 2s
  cache:
    type: redis
    redis:
      time-to-live: 5m
      cache-null-values: false
```

`@EnableCaching` on the main class:
```java
@SpringBootApplication
@EnableCaching
@ConfigurationPropertiesScan
public class TaskforgeApplication { ... }
```

> Spring Boot auto-configures the `RedisConnectionFactory`, the
> `RedisCacheManager`, and the `CacheManager` you can use with
> `@Cacheable`.

---

## 4. The three annotations

| Annotation | Effect |
|-----------|--------|
| `@Cacheable("tasks")` | Run the method, store the result in cache `tasks` |
| `@CacheEvict("tasks")` | After the method runs, remove one or all entries |
| `@CachePut("tasks")` | Always run the method, then update the cache |

`TaskService`:
```java
@Cacheable(value = "tasks", key = "#id")
@Transactional(readOnly = true)
public Task get(Long id) {
    return repo.findById(id).orElseThrow(() -> new NotFoundException("Task " + id));
}

@CacheEvict(value = "tasks", key = "#id")
public Task update(Long id, String title, String description, boolean done, Long requesterId) {
    // ...
}

@CacheEvict(value = "tasks", key = "#id")
public void delete(Long id) { ... }
```

> **`key = "#id"`** uses SpEL to refer to the method parameter named `id`.
> For multiple params: `key = "#ownerId + ':' + #priority"`.

> **Important caveat:** for `@Cacheable` to fire, the call must come
> through a Spring proxy — i.e. from outside the class. Internal
> `this.get(id)` calls bypass the cache. (A common surprise.)

---

## 5. Cache keys and serialization

By default, Spring stores cache values using a `JdkSerializationRedisSerializer`
— meaning **your cached objects must implement `Serializable`**.

For records (and JPA entities — proxies, lazy fields, etc.), use a JSON
serializer instead:

```java
@Bean
public RedisCacheManagerBuilderCustomizer jsonCacheManager() {
    return builder -> builder
        .cacheDefaults(RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(5))
            .disableCachingNullValues()
            .serializeValuesWith(SerializationPair.fromSerializer(new GenericJackson2JsonRedisSerializer())));
}
```

> `GenericJackson2JsonRedisSerializer` writes the class name as a `@class`
> field, so the bytes can be deserialized back to the right type. Don't
> use it for **entities with lazy associations** — they'd N+1 on
> deserialization. Cache DTOs, not entities.

---

## 6. What to cache and what not to

| Cache it | Don't cache it |
|----------|---------------|
| Read-heavy, slowly-changing data | Data that changes every write |
| Lookups by primary key | Scans (`findAll`, searches) |
| Computed results (e.g. `countByOwner`) | Anything that needs to be 100% fresh |
| Read-mostly aggregates | Personally-identifiable data with strict freshness rules |

For `taskforge`, cache:
- `taskforge.tasks` — individual task lookups by id.
- `taskforge.userTasks` — the "your open tasks" feed (per-user).

Don't cache the result of `repo.findAll()` or full-text search.

---

## 7. Cache invalidation — the **two hard things**

There are only two hard things in computer science: cache invalidation,
naming things, and off-by-one errors. Here's the invalidation playbook:

**Single entity updates** — evict by id:
```java
@CacheEvict(value = "tasks", key = "#id")
public Task update(Long id, ...) { ... }
```

**List endpoints** — keep TTLs short, or evict the whole cache:
```java
@CacheEvict(value = "userTasks", allEntries = true)
public Task create(...) { ... }
```

**Bulk updates** — `@CacheEvict(allEntries = true)` on the affected cache.

> **Conservative defaults:** if you're not sure, set a short TTL (1–5 min)
> and let entries expire on their own. **Stale cache is the most common
> caching bug.**

---

## 8. Conditional caching

`@Cacheable` has `condition` and `unless` for fine control:

```java
@Cacheable(value = "tasks", key = "#id", unless = "#result == null")
public Task get(Long id) { ... }
```

`#result` refers to the method's return value (after the method runs).
`#root` is the full `MethodInvocationContext` if you need more.

---

## 9. Programmatic caching with `RedisTemplate`

For things `@Cacheable` can't express — atomic counters, sorted sets,
pub/sub — drop down to `RedisTemplate`:

```java
@Service
public class PresenceService {
    private final RedisTemplate<String, String> redis;

    public PresenceService(RedisTemplate<String, String> redis) { this.redis = redis; }

    public void markOnline(Long userId) {
        redis.opsForValue().set("presence:" + userId, "online", Duration.ofMinutes(5));
    }

    public boolean isOnline(Long userId) {
        return "online".equals(redis.opsForValue().get("presence:" + userId));
    }
}
```

> `RedisTemplate` is the **lower-level** API. Use `@Cacheable` for
> method-level caching; use `RedisTemplate` for "Redis is part of my
> domain."

---

## 10. Multi-level caching

For really hot data, layer a **Caffeine in-memory cache** in front of
Redis:

```java
@Bean
public CacheManager cacheManager() {
    CompositeCacheManager composite = new CompositeCacheManager(
        new CaffeineCacheManager("tasks"),     // L1: in-process
        new RedisCacheManager(...));            // L2: shared
    composite.setFallbackToNoOpCache(true);
    return composite;
}
```

`Caffeine` is **fast** (in-process, no network) but **not shared** across
instances. Redis is the **source of truth** for the cache.

For this course, Redis alone is enough.

---

## 11. The `taskforge` cache wiring (summary)

```
TaskController.get(id)
  ▼
TaskService.get(id)             @Cacheable("tasks", key="#id")
  ▼ (cache miss)                @Cacheable("tasks", key="#id")
TaskRepository.findById(id)     ~3 ms
  ▼
Redis: set task:1 TTL=5m        ~0.5 ms
  ▼
return

TaskController.update(id, ...)
  ▼
TaskService.update(id, ...)     @CacheEvict("tasks", key="#id")
  ▼
Postgres UPDATE                 ~5 ms
  ▼
Redis: delete task:1
```

---

## 12. Testing cached code

Two strategies:

**1. Use a real Redis (Testcontainers):**
```java
@SpringBootTest
@Testcontainers
class CachedTaskServiceIT {
    @Container static GenericContainer<?> redis = new GenericContainer<>("redis:7").withExposedPorts(6379);
    @DynamicPropertySource static void p(DynamicPropertyRegistry r) {
        r.add("spring.data.redis.host", redis::getHost);
        r.add("spring.data.redis.port", () -> redis.getMappedPort(6379));
    }
    @Autowired TaskService service;
    @Autowired TaskRepository repo;
    @Autowired CacheManager cacheManager;

    @Test
    void secondCallHitsCache() {
        var t1 = service.create("a", "...", 1L);
        service.get(t1.getId());    // miss → DB
        service.get(t1.getId());    // hit
        // assert Redis has the key
    }
}
```

**2. Disable caching in unit tests** — `@Profile("!test")` on the cache
config, or use `spring.cache.type=none` in `application-test.yml`.

---

## 13. Common pitfalls

| Symptom | Cache returns stale data | You forgot `@CacheEvict` on the update method |
| Symptom | `SerializationException` | Cached object isn't `Serializable` and you didn't switch to JSON serialization |
| Symptom | `@Cacheable` does nothing | The call is `this.method(...)` from inside the same class — bypasses the proxy |
| Symptom | Cache works in dev, fails in prod | Redis URL wasn't externalized; the prod profile points at a different host |
| Symptom | `RedisCommandTimeoutException` | Pool is too small under load; `lettuce.pool.max-active=20` |
| Symptom | Memory grows unbounded | No TTL; every key is unique; set `time-to-live` |

---

## 14. Do the lab

Wire Redis caching for the `tasks` cache, evict on update/delete, and prove
with `redis-cli` that the cache is populated and invalidated.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

cache · cache-aside · `@Cacheable` · `@CacheEvict` · `@CachePut` · TTL · `RedisTemplate` · `RedisCacheManager` · SpEL key · invalidation · Caffeine · serialization

**Next →** [Module 11: Async Messaging with Kafka](../11-async-messaging/)

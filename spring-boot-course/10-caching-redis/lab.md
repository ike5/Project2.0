# Lab 10 — Cache Tasks in Redis

**You'll:** add Redis caching to `TaskService.get(...)`, evict on
`update(...)` and `delete(...)`, and prove the cache is working with
`redis-cli`.

⏱️ ~40 min. Run from `spring-boot-course/apps/taskforge`. The Redis
container from Module 00 must be up.

---

## Part A — Dependencies and config

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

`application.yml` (add to the `spring:` block):
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

---

## Part B — JSON-serialized cache (so entities round-trip cleanly)

`src/main/java/com/taskforge/config/CacheConfig.java`:
```java
package com.taskforge.config;

import org.springframework.boot.autoconfigure.cache.RedisCacheManagerBuilderCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializationContext.SerializationPair;

import java.time.Duration;

@Configuration
public class CacheConfig {

    @Bean
    public RedisCacheManagerBuilderCustomizer cacheCustomizer() {
        return builder -> builder
            .cacheDefaults(RedisCacheConfiguration.defaultCacheConfig()
                .entryTtl(Duration.ofMinutes(5))
                .disableCachingNullValues()
                .serializeValuesWith(SerializationPair.fromSerializer(
                    new GenericJackson2JsonRedisSerializer())));
    }
}
```

> This serializes cached entries as JSON (with a `@class` field for
> deserialization). Drop-in alternative to the JDK serializer.

---

## Part C — Annotate the service

`src/main/java/com/taskforge/task/TaskService.java`:
```java
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;

@Service
@Transactional
public class TaskService {

    private final TaskRepository repo;

    public TaskService(TaskRepository repo) { this.repo = repo; }

    @Cacheable(value = "tasks", key = "#id", unless = "#result == null")
    @Transactional(readOnly = true)
    public Task get(Long id) {
        return repo.findById(id).orElseThrow(() -> new NotFoundException("Task " + id));
    }

    public Task create(String title, String description, Long ownerId) {
        if (title == null || title.isBlank()) throw new IllegalArgumentException("title is required");
        Task t = new Task(title.trim(), description);
        t.setOwnerId(ownerId);
        return repo.save(t);
    }

    @CacheEvict(value = "tasks", key = "#id")
    public Task update(Long id, String title, String description, boolean done, Long requesterId) {
        Task t = get(id);
        if (!Objects.equals(t.getOwnerId(), requesterId))
            throw new ForbiddenException("not your task");
        if (title != null) t.setTitle(title);
        if (description != null) t.setDescription(description);
        t.setDone(done);
        return repo.save(t);
    }

    @CacheEvict(value = "tasks", key = "#id")
    public void delete(Long id) {
        if (!repo.existsById(id)) throw new NotFoundException("Task " + id);
        repo.deleteById(id);
    }

    @Transactional(readOnly = true)
    public List<Task> listForUser(Long ownerId) { return repo.findByOwnerId(ownerId); }
}
```

> **Important:** `@Cacheable` is on `get(...)` only. `create(...)` doesn't
> cache the *new* task — the next `get(id)` will populate it.

---

## Part D — Run and verify the cache

```bash
mvn -q spring-boot:run
```

In another terminal:
```bash
# 1. Get a token and create a task
TOKEN=$(curl -s -X POST localhost:8080/api/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"ann@example.com","password":"password123"}' | jq -r .accessToken)

TID=$(curl -s -X POST localhost:8080/api/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"title":"first"}' | jq -r .id)

# 2. First GET — cache miss
curl -s -H "Authorization: Bearer $TOKEN" localhost:8080/api/tasks/$TID

# 3. Inspect Redis
docker compose -f ../../00-setup/compose.dev.yml exec redis redis-cli
> KEYS *
> TTL "tasks::$TID"
> GET "tasks::$TID"     # JSON of the task
> exit

# 4. Update the task → cache evicted
curl -s -X PUT -H "Authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"title":"renamed"}' localhost:8080/api/tasks/$TID

# 5. Key is gone
docker compose -f ../../00-setup/compose.dev.yml exec redis redis-cli
> KEYS *                # no "tasks::$TID"
> exit

# 6. Next GET repopulates it
curl -s -H "Authorization: Bearer $TOKEN" localhost:8080/api/tasks/$TID
docker compose -f ../../00-setup/compose.dev.yml exec redis redis-cli
> KEYS *                # back!
> exit
```

✅ **Checkpoint:** the cache key appears after the first `GET`, is removed
on `PUT`, and is repopulated on the next `GET`.

---

## What you learned

- `@Cacheable` puts the result in Redis; `@CacheEvict` removes it.
- Cache keys default to `<cacheName>::<SpEL-key>` — easy to inspect.
- TTLs prevent unbounded growth; pick 1–10 min for "warm reads."
- JSON serialization (via `GenericJackson2JsonRedisSerializer`) handles
  modern types cleanly; the default JDK serializer requires `Serializable`.
- Cache invalidation goes on every **write** path that affects the
  cached data. Miss one and you have stale reads.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 11](../11-async-messaging/).

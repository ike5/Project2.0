# Solutions — Module 02

---

## Task 1 — Override an auto-configured bean

```java
package com.pulse.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.connection.RedisConnectionFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.StringRedisSerializer;

@Configuration
public class RedisConfig {

    @Bean
    public RedisTemplate<String, String> redisTemplate(RedisConnectionFactory cf) {
        var template = new RedisTemplate<String, String>();
        template.setConnectionFactory(cf);
        template.setKeySerializer(new StringRedisSerializer());
        template.setHashKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(new GenericJackson2JsonRedisSerializer());
        template.setHashValueSerializer(new GenericJackson2JsonRedisSerializer());
        return template;
    }
}
```

Before:
```bash
curl -s localhost:8080/actuator/conditions \
  | jq '.contexts.pulse.positiveMatches["RedisAutoConfiguration#redisTemplate"]'
```
```json
[{ "condition": "OnBeanCondition",
   "message": "@ConditionalOnMissingBean (names: redisTemplate; types: ...RedisTemplate) did not find any beans" }]
```

After:
```bash
curl -s localhost:8080/actuator/conditions \
  | jq '.contexts.pulse.negativeMatches["RedisAutoConfiguration#redisTemplate"]'
```
```json
{ "notMatched": [{ "condition": "OnBeanCondition",
    "message": "@ConditionalOnMissingBean (names: redisTemplate; ...) found beans of type 'org.springframework.data.redis.core.RedisTemplate' redisTemplate" }],
  "matched": [] }
```

✅ The entry **moved from `positiveMatches` to `negativeMatches`**, and the
message changed from "did not find any beans" to "found beans ... `redisTemplate`".

### Why the default uses JDK serialization, and why that's wrong here

Prove it first:

```bash
# default JdkSerializationRedisSerializer
redis-cli --no-raw GET "\xac\xed\x00\x05t\x00\x08presence"
```
```
"\xac\xed\x00\x05t\x00\x06online"
```
```bash
# with StringRedisSerializer + Jackson
redis-cli GET presence:42
```
```
"\"online\""
```

**Two sentences:**

> `RedisTemplate` defaults to `JdkSerializationRedisSerializer` because it's the
> only serializer that can round-trip an arbitrary `Object` without knowing its
> type — a safe default for a general-purpose template with `<Object, Object>`
> generics. It's wrong for Pulse because the keys become binary garbage you
> can't inspect with `redis-cli`, the payloads are ~3× larger, only JVM clients
> can read them, and any change to a class's `serialVersionUID` silently breaks
> every value already in Redis.

That last point matters operationally: with JDK serialization, a rolling deploy
where two versions of a class coexist produces `InvalidClassException` on
whichever node reads the other's data. JSON just works.

> **Security footnote:** JDK deserialization of untrusted data is a well-known
> RCE vector. Redis contents are semi-trusted, but "the cache is a code
> execution surface" is not a sentence you want to defend in a review.

---

## Task 2 — `SessionRegistry` as a bean, and the singleton trap

```java
@Configuration
public class RegistryConfig {
    @Bean
    public SessionRegistry sessionRegistry() {
        return new ConcurrentSessionRegistry();
    }
}
```

```java
@RestController
@RequestMapping("/rooms")
public class RoomSessionsController {
    private final SessionRegistry registry;
    RoomSessionsController(SessionRegistry registry) { this.registry = registry; }

    @GetMapping("/{roomId}/sessions")
    public Set<String> sessions(@PathVariable String roomId) {
        return registry.sessionsInRoom(roomId);
    }
}
```

### Singleton proof

```java
@SpringBootTest
class SingletonScopeTest {

    @Component static class CollaboratorA {
        final SessionRegistry registry;
        CollaboratorA(SessionRegistry r) { this.registry = r; }
    }
    @Component static class CollaboratorB {
        final SessionRegistry registry;
        CollaboratorB(SessionRegistry r) { this.registry = r; }
    }

    @Autowired CollaboratorA a;
    @Autowired CollaboratorB b;
    @Autowired ApplicationContext ctx;

    @Test
    void sameInstanceEverywhere() {
        assertSame(a.registry, b.registry, "not a singleton");
        assertSame(a.registry, ctx.getBean(SessionRegistry.class));
        assertTrue(ctx.getBeanFactory()
                .getBeanDefinition("sessionRegistry").isSingleton());
    }
}
```

### The mutable-field race

Add the bug:
```java
private int connectCount;                      // NOT thread-safe
public void connect(String sid, String uid) {
    // ... existing logic ...
    connectCount++;                            // read-modify-write, unsynchronized
}
public int connectCount() { return connectCount; }
```

Demonstrate:
```java
@Test
void mutableFieldIsARace() throws Exception {
    var latch = new CountDownLatch(1);
    int n = 100_000;
    try (var ex = Executors.newVirtualThreadPerTaskExecutor()) {
        for (int i = 0; i < n; i++) {
            final int id = i;
            ex.submit(() -> { latch.await(); registry.connect("s-" + id, "u"); return null; });
        }
        latch.countDown();
    }
    assertEquals(n, registry.connectCount());   // FAILS
}
```

**Expected failure:**
```
org.opentest4j.AssertionFailedError: expected: <100000> but was: <97843>
```

✅ ~2,000 increments vanished. `count++` is three operations (load, add, store)
and two threads can interleave between them.

**Fix — `LongAdder`:**
```java
private final LongAdder connectCount = new LongAdder();
public int connectCount() { return connectCount.intValue(); }
```
```
Test passed: 100000
```

`AtomicInteger` also works and is correct; `LongAdder` is faster under high
contention because it shards across cells and only sums on read — exactly the
read-rare/write-hot profile of a connection counter.

> **The general rule, restated:** a `@Service` is a singleton shared by every
> concurrent request. On a REST app with 200 Tomcat threads you might get away
> with sloppiness. With 50,000 virtual threads you will not.

---

## Task 3 — A health indicator that fails readiness but not liveness

```java
package com.pulse.health;

import org.springframework.boot.actuate.health.Health;
import org.springframework.boot.actuate.health.HealthIndicator;
import org.springframework.stereotype.Component;
import java.util.concurrent.atomic.AtomicLong;

@Component("fanoutBacklog")
public class FanoutBacklogHealthIndicator implements HealthIndicator {

    private final AtomicLong backlog = new AtomicLong();
    private final long threshold;

    public FanoutBacklogHealthIndicator(
            @Value("${pulse.health.backlog-threshold:10000}") long threshold) {
        this.threshold = threshold;
    }

    public void set(long v) { backlog.set(v); }

    @Override
    public Health health() {
        long current = backlog.get();
        var builder = current > threshold ? Health.down() : Health.up();
        return builder.withDetail("backlog", current)
                      .withDetail("threshold", threshold)
                      .build();
    }
}
```

Wire it into readiness only:

```yaml
management:
  endpoint:
    health:
      probes:
        enabled: true
      group:
        readiness:
          include: readinessState,db,redis,fanoutBacklog
        liveness:
          include: livenessState        # deliberately NOT fanoutBacklog
```

Verify:
```bash
curl -s localhost:8080/actuator/health/readiness | jq -r .status   # DOWN
curl -s localhost:8080/actuator/health/liveness  | jq -r .status   # UP
```

### Why backlog must never affect liveness

**The cascade:**

1. Traffic spikes. The fan-out backlog climbs past the threshold on all three
   nodes — it's a *load* condition, so it hits everyone at once.
2. Liveness turns `DOWN`. Kubernetes' kubelet (or Docker's healthcheck) does
   what liveness means: **it kills the container**.
3. The node restarts. It drops every WebSocket connection it held.
4. Those clients reconnect — to the two remaining nodes, which were already
   backlogged.
5. Their backlog grows faster. They fail liveness. They get killed.
6. Repeat until every node is in `CrashLoopBackOff` and the service is
   *completely* down — having started from "somewhat slow."

The restarted node also comes back **cold**: empty caches, a fresh JVM in
interpreted mode, and a thundering herd of reconnects pointed at it. It is
strictly less capable of handling the backlog than the node you just killed.

**The rule:**

> **Liveness** answers "is this process wedged such that only a restart can
> help?" — a deadlock, an unrecoverable `OutOfMemoryError`, a corrupted internal
> state machine. It should be nearly constant.
>
> **Readiness** answers "should I get *new* work right now?" Load conditions,
> backlogs, dependency outages, and warm-up all belong here, because the correct
> response is *stop sending traffic*, not *destroy the process*.

Conflating them turns every capacity problem into an availability incident.

---

## Task 4 — Admission control

```java
package com.pulse.web;

import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import java.util.concurrent.*;

@RestController
public class AdmissionController {

    private final Semaphore permits = new Semaphore(50, true);   // fair: FIFO

    @GetMapping("/work")
    public ResponseEntity<String> work() throws InterruptedException {
        if (!permits.tryAcquire(2, TimeUnit.SECONDS)) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                    .header(HttpHeaders.RETRY_AFTER, "1")
                    .body("overloaded");
        }
        try {
            Thread.sleep(50);                     // the "database call"
            return ResponseEntity.ok("done");
        } finally {
            permits.release();
        }
    }
}
```

```bash
# without admission control (permits = 10000)
k6 run --vus 500 --duration 30s script.js
# with admission control (permits = 50)
k6 run --vus 500 --duration 30s script.js
```

Reference results:

| | Throughput | p50 | p99 | 503s |
|---|-----------|-----|-----|------|
| No admission control | 985 req/s | 486 ms | 1,240 ms | 0 |
| Admission control (50, 2 s timeout) | 981 req/s | 51 ms | 118 ms | 4,120 |

**Reading this correctly:** throughput is essentially identical — the work
capacity didn't change. What changed is that **the requests that were going to
be slow anyway now fail fast and say so**, instead of silently degrading
everyone's latency.

Two design notes:

- `new Semaphore(50, true)` — **fairness matters here.** An unfair semaphore is
  faster but permits barging, so under sustained overload some requests starve
  indefinitely while others sail through. That produces a p99.9 that looks like
  a random number generator.
- `Retry-After` is not decoration. Without it, well-behaved clients retry
  immediately and you've converted overload into a retry storm — which is the
  thundering herd again, in miniature.

> **This is the practical form of Module 01's lesson.** Virtual threads let all
> 500 requests start. Something has to decide that only 50 proceed, and if you
> don't decide, the decision gets made for you by whatever runs out first.

---

## Task 5 — Profiles

`src/main/resources/application-bench.yml`:
```yaml
spring:
  datasource:
    hikari:
      maximum-pool-size: 50
  jpa:
    open-in-view: false

logging:
  level:
    root: WARN
    com.pulse: WARN
```

```bash
./mvnw spring-boot:run -Dspring-boot.run.profiles=bench
# or
SPRING_PROFILES_ACTIVE=bench java -jar target/pulse-0.0.1-SNAPSHOT.jar
```

Prove it took effect — don't trust the log line:
```bash
curl -s localhost:8080/actuator/env | jq -r '.activeProfiles[]'
curl -s localhost:8080/actuator/configprops \
  | jq '.contexts.pulse.beans | to_entries[]
        | select(.key|test("Hikari|DataSource"))
        | .value.properties.maximumPoolSize' 
```
**Expected:**
```
bench
50
```

Also confirm the underlying pool, not just the config:
```bash
curl -s localhost:8080/actuator/metrics/hikaricp.connections.max | jq '.measurements[0].value'
```
```
50
```

> `/actuator/configprops` shows what was *bound*; the metric shows what the pool
> actually *did*. When they disagree — and they occasionally do, when something
> reconfigures the pool programmatically — believe the metric.

---

## Task 6 (stretch) — Startup profiling

```bash
java -Dspring.context.startup=true -jar target/pulse-0.0.1-SNAPSHOT.jar
curl -s localhost:8080/actuator/startup | jq '
  [ .timeline.events[]
    | { name: .startupStep.name,
        tag: (.startupStep.tags[]? | select(.key=="beanName") | .value),
        ms: .duration } ]
  | sort_by(-.ms) | .[0:5]'
```

**Expected:**
```json
[
  { "name": "spring.beans.instantiate", "tag": "entityManagerFactory",  "ms": 743 },
  { "name": "spring.beans.instantiate", "tag": "flywayInitializer",     "ms": 312 },
  { "name": "spring.beans.instantiate", "tag": "dataSource",            "ms": 198 },
  { "name": "spring.beans.instantiate", "tag": "tomcatServletWebServerFactory", "ms": 156 },
  { "name": "spring.beans.instantiate", "tag": "redisConnectionFactory","ms": 88 }
]
```

**The three slowest:**

1. **`entityManagerFactory` (743 ms)** — Hibernate scanning entities, building
   metamodel, validating the schema against the database. Dominates every JPA
   app's startup.
2. **`flywayInitializer` (312 ms)** — connecting, checksumming migrations,
   reading `flyway_schema_history`. Grows with migration count.
3. **`dataSource` (198 ms)** — Hikari opening its initial connections.

AOT comparison:
```bash
./mvnw -Pnative -DskipTests spring-boot:process-aot package
```

| Build | Startup |
|-------|---------|
| Standard JVM | 2.18 s |
| JVM + AOT | 1.51 s (−31%) |
| GraalVM native image | 0.09 s |

**Does this matter for Pulse?** Mostly no, and it's worth being clear about why:
a chat server is long-lived, and 2 seconds of startup is irrelevant next to the
hours it then runs. It matters in exactly two places in this course — Module 18,
where slow startup lengthens the window during which a restarted node isn't
taking connections, and Module 19, where `startupProbe` timings depend on it.

Native image is a poor fit here for a different reason: it trades peak
throughput for startup, and the JIT's peak throughput is precisely what a
long-running fan-out server wants.

# Module 15 — Observability with Actuator, Metrics, and Health

**Goal:** make `taskforge` **legible to operators** — expose health checks
for every dependency, instrument business metrics, and emit traces that
follow a request end-to-end. By the end, you can answer "is the system
healthy?" and "where is it slow?" in seconds.

⏱️ ~2 hours · 🎯 Prereq: Modules 02–14 complete (containerized app).

> Observability is what turns a deployed system from a black box into a
> service you can run. Three pillars: **logs** (Module 09), **metrics**
> (this module), **traces** (this module).

---

## 1. The three pillars

| Pillar | Question it answers | Tool |
|--------|---------------------|------|
| **Logs** | What happened in this request? | Logback → JSON → Loki/ES/CloudWatch (Module 09) |
| **Metrics** | How is the system doing over time? | Micrometer → Prometheus → Grafana |
| **Traces** | Where did the time go in this request? | Micrometer Tracing → OpenTelemetry → Jaeger/Tempo |

You already have logs (Module 09). This module adds metrics and traces.

---

## 2. Spring Boot Actuator — the ops endpoints

Add (you already have this from Module 02):
```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
```

Expose what you need (the more you expose, the more an attacker sees):
```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  endpoint:
    health:
      probes:
        enabled: true                       # liveness + readiness
      show-details: when-authorized         # or "always" in dev
  health:
    db:
      enabled: true                         # auto: JDBC ping
    redis:
      enabled: true                         # auto: PING
    kafka:
      enabled: true                         # auto: admin client
    diskspace:
      enabled: true
```

`/actuator/health` aggregates:
```json
{
  "status": "UP",
  "components": {
    "db":    { "status": "UP" },
    "redis": { "status": "UP" },
    "kafka": { "status": "UP" },
    "diskSpace": { "status": "UP", "details": { "free": "23GB", "total": "100GB" } }
  }
}
```

If anything is `DOWN`, the aggregate is `DOWN`. Docker / K8s read this
to decide whether to send traffic.

---

## 3. Liveness vs readiness

Two separate endpoints, two different questions:

- **Liveness** — "is the process alive?" Failure → restart it.
  - `GET /actuator/health/liveness`
- **Readiness** — "is the process ready to serve?" Failure → take it out
  of the load balancer.
  - `GET /actuator/health/readiness`

By default, liveness is "the app is running"; readiness is "the
dependencies are up." You can add custom indicators:

```java
@Component
public class TaskMigrationHealthIndicator implements HealthIndicator {
    private final Flyway flyway;
    public TaskMigrationHealthIndicator(Flyway flyway) { this.flyway = flyway; }

    @Override
    public Health health() {
        var applied = flyway.info().applied();
        if (applied.length == 0) return Health.down().withDetail("reason", "no migrations applied").build();
        return Health.up().withDetail("latest", applied[applied.length - 1].getVersion()).build();
    }
}
```

Module 14's Docker `HEALTHCHECK` uses the aggregate `/actuator/health`
endpoint. In Kubernetes, `livenessProbe` and `readinessProbe` should
point at the split endpoints.

---

## 4. Metrics — the Micrometer API

Spring Boot's metrics are built on **Micrometer**, a vendor-neutral API
(think SLF4J for metrics). The Prometheus format is one of many "rigs"
Micrometer can speak.

```xml
<dependency>
  <groupId>io.micrometer</groupId>
  <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>
```

That single dependency adds a `/actuator/prometheus` endpoint that emits:
- `jvm_memory_used_bytes{area="heap"}` — JVM memory by area.
- `http_server_requests_seconds{uri="/api/tasks",method="POST",status="201"}` — every HTTP request as a timer.
- `hikaricp_connections_active{pool="HikariPool-1"}` — connection pool stats.
- `kafka_producer_record_send_total` — Kafka producer counts.

This is the data Prometheus scrapes and Grafana plots.

---

## 5. Custom metrics — counters, gauges, timers

Inject `MeterRegistry`:

```java
@Service
public class TaskService {
    private final MeterRegistry metrics;

    public TaskService(TaskRepository repo, MeterRegistry metrics) {
        this.repo = repo;
        this.metrics = metrics;
    }

    public Task create(String title, String description, Long ownerId) {
        // ...
        metrics.counter("taskforge.tasks.created").increment();
        return saved;
    }

    @Timed(value = "taskforge.task.update", description = "Time to update a task")
    public Task update(...) { ... }
}
```

> **`@Timed`** is a method-level annotation that wraps the call in a
> timer. The result is `taskforge_task_update_seconds_count` and `_sum`.

View your custom metric:
```bash
curl -s localhost:8080/actuator/metrics/taskforge.tasks.created
# → {"name":"taskforge.tasks.created","measurements":[{"statistic":"COUNT","value":3.0}]}
```

In Prometheus format:
```bash
curl -s localhost:8080/actuator/prometheus | grep taskforge
# → taskforge_tasks_created_total 3.0
```

---

## 6. Tagging — the dimension system

Counters and timers have **tags** (Prometheus calls them *labels*):

```java
Counter.builder("taskforge.tasks.created")
    .tag("priority", priority)
    .description("Number of tasks created")
    .register(metrics)
    .increment();
```

Now you can ask: "how many `high`-priority tasks were created today?"
```promql
sum(taskforge_tasks_created_total{priority="high"})
```

> **Cardinality warning:** don't tag with unbounded values (user ids,
> request ids, etc.). The cardinality of a metric is the number of unique
> combinations of tags — high cardinality wrecks Prometheus.

Good tag values: `priority`, `status`, `result`, `endpoint`, `method`,
`role`. Bad: `userId`, `requestId`, `email`.

---

## 7. Tracing — Micrometer Tracing + OpenTelemetry

Distributed tracing follows a request across processes: API → DB → Kafka →
worker. **Trace id** identifies the whole journey; **span id** identifies
a single step.

Add:
```xml
<dependency>
  <groupId>io.micrometer</groupId>
  <artifactId>micrometer-tracing-bridge-otel</artifactId>
</dependency>
<dependency>
  <groupId>io.opentelemetry</groupId>
  <artifactId>opentelemetry-exporter-zipkin</artifactId>
</dependency>
```

`application.yml`:
```yaml
management:
  tracing:
    sampling:
      probability: 1.0       # 100% in dev; lower (0.05–0.1) in prod
  zipkin:
    tracing:
      endpoint: http://localhost:9411/api/v2/spans
```

> In production, swap Zipkin for **OpenTelemetry Collector** → **Tempo** /
> **Jaeger** / **Datadog**. The Spring config is the same.

The `traceId` from Module 09 is now an **OpenTelemetry trace id** — the
same one shown in Jaeger.

---

## 8. `@Observed` — instrument a method

```java
@Observed(name = "task.create", contextualName = "createTask")
public Task create(String title, String description, Long ownerId) {
    // ...
}
```

With `management.observations.annotations.enabled: true`, every call
appears as a span in the trace and a timer in `/actuator/prometheus`.

---

## 9. Putting it together — the Prometheus + Grafana stack

`docker-compose.yml` (additions):
```yaml
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
```

`prometheus.yml`:
```yaml
global:
  scrape_interval: 5s
scrape_configs:
  - job_name: 'taskforge'
    metrics_path: /actuator/prometheus
    static_configs:
      - targets: ['app:8080']
```

Open <http://localhost:9090> (Prometheus) and run:
```promql
rate(taskforge_tasks_created_total[1m])
```

Open <http://localhost:3000> (Grafana, login `admin`/`admin`), add
Prometheus as a data source at `http://prometheus:9090`, and build a
dashboard.

---

## 10. Custom health indicators — when the DB is reachable but degraded

The built-in `db` indicator checks if Postgres is reachable. You might
also want to know "is the connection pool exhausted?":

```java
@Component
public class ConnectionPoolHealthIndicator implements HealthIndicator {
    private final HikariDataSource ds;
    public ConnectionPoolHealthIndicator(DataSource ds) {
        this.ds = (HikariDataSource) ds;
    }

    @Override
    public Health health() {
        var mx = ds.getHikariPoolMXBean();
        int active = mx.getActiveConnections();
        int total  = ds.getMaximumPoolSize();
        if (active >= total) return Health.down().withDetail("pool", active + "/" + total).build();
        return Health.up().withDetail("pool", active + "/" + total).build();
    }
}
```

> Hikari's Micrometer integration already exposes these as metrics; the
> health indicator is the **alarm**.

---

## 11. Common pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `/actuator/prometheus` returns `404` | `micrometer-registry-prometheus` isn't on the classpath | Add the dependency |
| Custom metric is missing | You used the wrong name format | Micrometer uses dots (`task.created`); Prometheus replaces with underscores (`task_created_total`) |
| Metrics are missing tags | You created the counter once at class level | Either tag at registration time or use `Counter.builder(...).tag(...)` per call |
| Tracing shows only the API | The other services (Kafka, MinIO) don't trace | Add tracing config to each Spring Boot app |
| High memory usage | Tracing 100% of traffic is heavy | Drop `management.tracing.sampling.probability` to `0.1` in prod |
| `/actuator/health` is `DOWN` after a transient error | Health checks are not sticky | By design — the next scrape should be `UP`. If it's not, the issue is real. |

---

## 12. Do the lab

Add the Prometheus dependency, a custom counter, a `@Timed` service
method, and bring up Prometheus + Grafana. Confirm a request shows up in
the dashboard.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

Actuator · `/actuator/health` · liveness · readiness · `HealthIndicator` · Micrometer · `MeterRegistry` · counter · gauge · timer · `@Timed` · `@Observed` · tags · cardinality · Prometheus · `/actuator/prometheus` · Micrometer Tracing · OpenTelemetry · trace id · span id · Zipkin · Jaeger · Grafana

**Next →** [Module 16: Capstone — Production-Ready App](../16-capstone/)

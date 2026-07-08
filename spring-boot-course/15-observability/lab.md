# Lab 15 — Health, Metrics, and a Dashboard

**You'll:** add Prometheus metrics, a custom counter, a `@Timed` method,
and bring up Prometheus + Grafana in `docker-compose`. Watch a custom
metric in real time.

⏱️ ~45 min. Run from `spring-boot-course/`. The full stack from Module 14
should be up.

---

## Part A — Add the dependencies

`pom.xml`:
```xml
<dependency>
  <groupId>io.micrometer</groupId>
  <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>
<dependency>
  <groupId>io.micrometer</groupId>
  <artifactId>micrometer-tracing-bridge-otel</artifactId>
</dependency>
<dependency>
  <groupId>io.opentelemetry</groupId>
  <artifactId>opentelemetry-exporter-zipkin</artifactId>
</dependency>
```

---

## Part B — Update `application.yml`

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  endpoint:
    health:
      probes:
        enabled: true
      show-details: always
  health:
    db:    { enabled: true }
    redis: { enabled: true }
    kafka: { enabled: true }
  tracing:
    sampling:
      probability: 1.0
  observations:
    annotations:
      enabled: true
  zipkin:
    tracing:
      endpoint: http://zipkin:9411/api/v2/spans
```

---

## Part C — Custom counter and `@Timed` in `TaskService`

```java
import io.micrometer.core.annotation.Timed;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;

@Service
@Transactional
public class TaskService {

    private final TaskRepository repo;
    private final TaskEventPublisher events;
    private final MeterRegistry metrics;
    private final Counter createdCounter;

    public TaskService(TaskRepository repo, TaskEventPublisher events, MeterRegistry metrics) {
        this.repo = repo;
        this.events = events;
        this.metrics = metrics;
        this.createdCounter = Counter.builder("taskforge.tasks.created")
            .description("Number of tasks created")
            .register(metrics);
    }

    @Timed(value = "taskforge.task.create", description = "Time to create a task")
    public Task create(String title, String description, Long ownerId) {
        // ...
        Task saved = repo.save(t);
        createdCounter.increment();
        events.publish(TaskEvent.created(saved, MDC.get("traceId")));
        return saved;
    }
}
```

---

## Part D — Add Prometheus + Grafana + Zipkin to `docker-compose.yml`

```yaml
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./observability/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin

  zipkin:
    image: openzipkin/zipkin:latest
    ports:
      - "9411:9411"
```

`observability/prometheus.yml`:
```yaml
global:
  scrape_interval: 5s
scrape_configs:
  - job_name: 'taskforge'
    metrics_path: /actuator/prometheus
    static_configs:
      - targets: ['app:8080']
```

```bash
mkdir -p observability
# create the file above
docker compose up -d
```

---

## Part E — Verify

```bash
# 1. Prometheus is scraping
curl -s localhost:9090/targets
# → "taskforge" job is "UP"

# 2. The custom metric is there
curl -s localhost:8080/actuator/metrics/taskforge.tasks.created
# → {"name":"taskforge.tasks.created","measurements":[{"statistic":"COUNT","value":...}]}

# 3. The Prometheus output has it
curl -s localhost:8080/actuator/prometheus | grep taskforge_tasks_created

# 4. Generate some traffic
TOKEN=$(curl -s -X POST localhost:8080/api/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"ann@example.com","password":"password123"}' | jq -r .accessToken)

for i in 1 2 3 4 5; do
  curl -s -X POST -H "Authorization: Bearer $TOKEN" -H 'content-type: application/json' \
    -d "{\"title\":\"task $i\"}" localhost:8080/api/tasks
done

# 5. Confirm the counter increased
curl -s localhost:8080/actuator/metrics/taskforge.tasks.created
# → "value":5.0
```

Open:
- <http://localhost:9090> → Prometheus; query
  `rate(taskforge_tasks_created_total[1m])`.
- <http://localhost:3000> → Grafana (login `admin`/`admin`); add Prometheus
  as a data source (`http://prometheus:9090`); build a dashboard.
- <http://localhost:9411> → Zipkin; find your recent trace by service
  `taskforge`.

✅ **Checkpoint:** metrics, traces, and dashboards are live. The custom
counter and the request timer are both visible in Prometheus.

---

## What you learned

- Actuator's `/actuator/health` aggregates dependency checks; liveness and
  readiness are separate endpoints for orchestrators.
- Micrometer + the Prometheus registry exposes JVM, HTTP, JDBC, and your
  custom metrics in a vendor-neutral API.
- `@Timed` is a one-line way to time a method; `@Observed` adds a span
  too.
- Prometheus scrapes, Grafana plots, Zipkin traces — three tools, one
  coherent observability stack.
- Tag with care: low cardinality, high value. Never tag with user ids or
  request ids.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 16](../16-capstone/).

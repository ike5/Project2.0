# Challenge 15 — Reference Solution

### 1. Liveness vs readiness
```bash
$ curl -s localhost:8080/actuator/health/liveness
{"status":"UP"}

$ docker compose stop redis
$ curl -s localhost:8080/actuator/health/readiness
{"status":"DOWN","components":{"redis":{"status":"DOWN"}}}

$ curl -s localhost:8080/actuator/health/liveness
{"status":"UP"}      # ← the process is alive, just not ready

$ docker compose start redis
```

### 2. Tagged counter
```java
Counter.builder("taskforge.tasks.created")
    .tag("result", "success").register(metrics).increment();
```
…or use a `Tags`-aware helper:
```java
metrics.counter("taskforge.tasks.created", "result", "success").increment();
metrics.counter("taskforge.tasks.created", "result", "error").increment();
```

### 3. Latency panel
```promql
histogram_quantile(0.50, sum(rate(http_server_requests_seconds_bucket{uri="/api/tasks",method="POST"}[5m])) by (le))
histogram_quantile(0.95, sum(rate(http_server_requests_seconds_bucket{uri="/api/tasks",method="POST"}[5m])) by (le))
histogram_quantile(0.99, sum(rate(http_server_requests_seconds_bucket{uri="/api/tasks",method="POST"}[5m])) by (le))
```

### 4. Connection pool health
```java
@Component
public class ConnectionPoolHealthIndicator implements HealthIndicator {
    private final HikariDataSource ds;
    public ConnectionPoolHealthIndicator(DataSource ds) { this.ds = (HikariDataSource) ds; }

    public Health health() {
        var mx = ds.getHikariPoolMXBean();
        int active = mx.getActiveConnections();
        int idle   = mx.getIdleConnections();
        int total  = ds.getMaximumPoolSize();
        return Health.up()
            .withDetail("active", active)
            .withDetail("idle", idle)
            .withDetail("max", total)
            .build();
    }
}
```

### 5. Kafka trace propagation
With `spring-kafka` 3.x and `micrometer-tracing-bridge-otel` on the
classpath, the trace id is automatically added to the Kafka record's
headers by `KafkaTemplate`. On the consumer side, `@KafkaListener`
extracts it and creates a child span.

Confirm by sending a request and looking at the trace in Zipkin — the
producer's span and the consumer's span are linked.

### 6. SLO alert (stretch)
`observability/prometheus-alerts.yml`:
```yaml
groups:
  - name: taskforge-slo
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_server_requests_seconds_count{status=~"5.."}[5m]))
            / sum(rate(http_server_requests_seconds_count[5m])) > 0.01
        for: 5m
        labels: { severity: page }
        annotations:
          summary: "taskforge error rate > 1% for 5m"
```
Add to `prometheus.yml`:
```yaml
rule_files:
  - /etc/prometheus/prometheus-alerts.yml
```
`docker compose restart prometheus`. Confirm the alert is loaded:
`curl localhost:9090/alerts`.

> The combination of metrics + traces + logs is what separates a service
> that "works on my machine" from a service that survives production.

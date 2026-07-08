# Lab 00 — Prove Your Environment Works

**You'll:** start the local data services, connect to Postgres and Redis by
hand, post and consume a Kafka message, peek at the mail and storage UIs, and
run the Hello Spring app.

⏱️ ~30 min. Run commands from `spring-boot-course/00-setup` unless noted.

---

## Part A — Bring up the data services

```bash
cd 00-setup
docker compose -f compose.dev.yml up -d
docker compose -f compose.dev.yml ps
```

✅ Expected: `postgres`, `redis`, `kafka`, `mailhog`, `minio` all `running`
(Postgres, Redis, Kafka, and MinIO show `healthy` after a few seconds).

---

## Part B — Talk to Postgres

Connect with `psql` *inside* the container (no local client needed):

```bash
docker compose -f compose.dev.yml exec postgres psql -U taskforge -d taskforge
```

Inside the prompt:
```sql
SELECT version();      -- PostgreSQL 16.x ...
\l                     -- list databases (you'll see "taskforge")
\q                     -- quit
```

✅ **Checkpoint:** you reached Postgres 16 with the `taskforge` user and
database that later modules' `application.yml` expects.

---

## Part C — Talk to Redis

```bash
docker compose -f compose.dev.yml exec redis redis-cli
```

Inside the prompt:
```
PING            -> PONG
SET hello world -> OK
GET hello       -> "world"
TTL hello       -> -1        (no expiry yet)
EXPIRE hello 30 -> 1         (this is how cache TTLs work in Module 10)
TTL hello       -> ~30
exit
```

✅ **Checkpoint:** Redis answers `PONG` and you set/read a key with a TTL —
the exact mechanism Module 10 uses for caching.

---

## Part D — Post and consume a Kafka message

Run the Kafka CLI inside the container:

```bash
# terminal 1 — start a consumer
docker compose -f compose.dev.yml exec kafka \
  kafka-console-consumer.sh --bootstrap-server localhost:9092 \
  --topic hello --from-beginning
```

```bash
# terminal 2 — produce a message
docker compose -f compose.dev.yml exec kafka \
  kafka-console-producer.sh --bootstrap-server localhost:9092 --topic hello
# type: hello from setup
# press Enter, then Ctrl-C
```

The consumer in terminal 1 prints `hello from setup`.

✅ **Checkpoint:** you produced a message to a topic and consumed it — the
exact pattern Module 11 builds on.

---

## Part E — Mail and storage dashboards

These back email (Module 12) and uploads (Module 12). Just confirm they load:

- Open <http://localhost:8025> → the **MailHog** inbox (empty for now).
- Open <http://localhost:9001> → the **MinIO** console; log in with
  `minioadmin` / `minioadmin`.

✅ **Checkpoint:** both UIs open. You don't need to do anything in them yet.

---

## Part F — Hello, Spring Boot

Create a tiny project and confirm Maven can resolve Spring Boot dependencies
and the embedded server starts:

```bash
mkdir -p /tmp/hello-spring && cd /tmp/hello-spring
# (or use IntelliJ: File → New → Project → Spring Initializr → Java 21, Maven,
#  Spring Web, then Run)
```

Save this as `src/main/java/com/example/hellospring/HelloSpringApplication.java`:

```java
package com.example.hellospring;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class HelloSpringApplication {
    public static void main(String[] args) {
        SpringApplication.run(HelloSpringApplication.class, args);
    }

    @GetMapping("/")
    public String hello() {
        return "Hello, Spring Boot!";
    }
}
```

And `pom.xml` (use [start.spring.io](https://start.spring.io) if you prefer
the GUI — Java 21, Maven, Spring Boot 3.3.x, dependency: `Spring Web`):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.3.4</version>
  </parent>
  <groupId>com.example</groupId>
  <artifactId>hellospring</artifactId>
  <version>0.0.1-SNAPSHOT</version>
  <properties>
    <java.version>21</java.version>
  </properties>
  <dependencies>
    <dependency>
      <groupId>org.springframework.boot</groupId>
      <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
  </dependencies>
</project>
```

Run it:
```bash
mvn -q spring-boot:run
# in another terminal:
curl -s localhost:8080/        # → "Hello, Spring Boot!"
```

Stop the app with `Ctrl-C`.

✅ **Checkpoint:** you stood up a Spring Boot app, Maven resolved all
transitive dependencies from the network, and the embedded Tomcat served a
real HTTP response.

---

## What you learned

- The app will depend on Postgres, Redis, Kafka, MailHog, and MinIO — all run
  locally in containers, all reachable from Spring Boot.
- You can reach Postgres with `psql`, Redis with `redis-cli`, and Kafka with
  `kafka-console-*` for debugging.
- Redis keys can carry a TTL — the basis for caching (Module 10).
- Spring Boot apps run with `mvn spring-boot:run`; the embedded server lives
  on `http://localhost:8080` by default.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 01](../01-java-fast-track/).

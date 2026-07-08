# Module 00 — Setup & Orientation

**Goal:** install the toolchain (JDK 21, Maven, IDE), start the local data
services (Postgres, Redis, Kafka, MailHog, MinIO) in Docker, and confirm
everything works end-to-end.

⏱️ ~1 hour · 🎯 By the end you'll have every tool installed, the data services
healthy, and a "Hello, Spring Boot" smoke test running.

> You won't write app code yet. This module gets the moving parts in place so
> every later lab "just works."

---

## 1. What we're installing and why

| Tool | What it is | Why we need it |
|------|-----------|----------------|
| **JDK 21 (LTS)** | Java Development Kit | Compiles and runs Java + Spring Boot |
| **Maven 3.9+** | Build & dependency tool | Builds the project, manages dependencies, runs tests |
| **IntelliJ IDEA** (Community) | IDE | Best-in-class Java/Spring support; Community is free |
| **VS Code** (alternative) | Editor | Lightweight; works with the "Extension Pack for Java" |
| **Docker** | Container runtime | Runs Postgres/Redis/Kafka/MailHog/MinIO locally |
| **curl / jq** | HTTP tools | Talk to your own API for testing |

> **Already done the [Docker primer](../../kubernetes-course/01-containers-docker/)?**
> Then containers, images, and `docker run` are familiar — we build on that
> here and won't re-explain the basics.

---

## 2. Install (Mac via Homebrew; Linux notes inline)

```bash
# Mac
brew install openjdk@21 maven
brew install --cask docker intellij-idea-ce    # then launch Docker.app once
brew install jq                                # for parsing JSON in the terminal

# Set JAVA_HOME for your shell (add to ~/.zshrc or ~/.bashrc)
echo 'export JAVA_HOME=$(/usr/libexec/java_home -v 21)' >> ~/.zshrc
echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.zshrc
source ~/.zshrc

# Linux (Debian/Ubuntu): use your package manager + the Adoptium PPA for JDK 21,
# and install Maven from apt or by downloading the binary.
```

Verify everything (see [VERIFY.md](../VERIFY.md) §0):

```bash
java --version      # openjdk 21.x ...
mvn --version       # Apache Maven 3.9.x ...
docker version      # Client AND Server sections
docker compose version
```

---

## 3. Run the data services locally

We develop against the same engines we ship: **Postgres 16**, **Redis 7**,
**Kafka 3.7** (KRaft mode, no ZooKeeper), **MailHog** (dev SMTP), and
**MinIO** (S3-compatible storage). The provided
[`compose.dev.yml`](./compose.dev.yml) starts all five in containers with
persistent volumes.

```bash
cd 00-setup
docker compose -f compose.dev.yml up -d
docker compose -f compose.dev.yml ps
```

✅ Expected: all five services running.
```
NAME       SERVICE    STATUS
postgres   postgres   running (healthy)
redis      redis      running (healthy)
kafka      kafka      running (healthy)
mailhog    mailhog    running
minio      minio      running (healthy)
```

Open the dashboards to prove they work:

- MailHog inbox → <http://localhost:8025>
- MinIO console → <http://localhost:9001> (user/pass `minioadmin`/`minioadmin`)

Stop them at the end of a session (data persists in named volumes):
```bash
docker compose -f compose.dev.yml stop
```

> **Why Kafka in dev?** Real apps use async messaging. We use Kafka from
> Module 11 onward. Having it running now means no setup surprises later.

---

## 4. Hello, Spring Boot — the first smoke test

Make sure Maven, Java, and the network work end-to-end by generating and
running a tiny app:

```bash
mkdir -p /tmp/hello-spring && cd /tmp/hello-spring
# Use the Spring Initializr CLI to scaffold (or visit start.spring.io in a browser)
mvn archetype:generate \
  -DarchetypeGroupId=org.springframework.boot \
  -DarchetypeArtifactId=spring-boot-starter-parent \
  -DarchetypeVersion=3.3.4
# (accept defaults; this takes a moment on first run)
```

If the interactive archetype is too noisy, just create a minimal project by
hand. Save the snippet below as `HelloSpringApplication.java`:

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

And a `pom.xml` that pulls in the Spring Boot parent and the web starter
(see Module 02 for the full file layout):

```bash
mvn -q spring-boot:run
# in another terminal:
curl -s localhost:8080/        # → "Hello, Spring Boot!"
```

✅ **Checkpoint:** you've just stood up a Spring Boot app with an embedded
Tomcat, autowired a JSON-returning controller, and resolved all the
transitive dependencies for the first time. Every later module starts from
this exact shape.

---

## 5. The big picture

Here's everything you'll build and how it connects. Keep this map in mind —
each module fills in one box.

```
                 Browser / curl / frontend
                          │
                       HTTP+JWT
                          │
                          ▼
                 ┌────────────────────┐
                 │   Spring Boot app  │
                 │  Controllers →     │
                 │  Services →        │
                 │  Repositories      │
                 └──┬───┬──────┬───┬──┘
                    │   │      │   │
                    ▼   ▼      ▼   ▼
                Postgres Redis Kafka MinIO
                 (data) (cache) (events) (files)
                    │
                    ▼
                MailHog (dev SMTP)
```

By the capstone:

- **Web** (Module 04) is the `@RestController` layer.
- **Security** (07) is the filter chain that validates JWTs.
- **Service** (03) is where business rules live.
- **Repository** (05) is Spring Data JPA over Postgres.
- **Cache** (10) sits in front of the database.
- **Kafka** (11) carries async events between services.
- **MinIO** (12) holds file attachments.
- **MailHog** (12) is where dev emails go.
- **Actuator** (15) exposes health + metrics.

---

## 6. Do the lab

Confirm the whole toolchain end-to-end: bring up the data services, connect
to Postgres and Redis by hand, post and consume a message in Kafka, peek at
the mail and storage UIs, and run the Hello Spring app.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

JDK · JVM · Maven · Spring Boot · starter · Docker · Postgres · Redis · Kafka · MailHog · MinIO

**Next →** [Module 01: Java Fast-Track for Spring](../01-java-fast-track/)

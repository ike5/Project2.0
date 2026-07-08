# Module 02 — Spring Boot Fundamentals

**Goal:** generate a real Spring Boot project with `start.spring.io`, understand
its layout, run it, and learn the three core ideas — **starters**, **auto-
configuration**, and the **main application class** — that every later module
builds on.

⏱️ ~2 hours · 🎯 Prereq: Modules 00–01 complete (JDK 21, Maven, Java fluency).

> This is the **first module** where the lab lives in the long-lived
> `apps/taskforge/` project. From here on, every module adds code to the same
> app; you don't start a new project per module.

---

## 1. The app we're building — `taskforge`

A small but realistic **task tracker** backend. Think of it as a stripped-down
Todoist / Jira:

- Users register and log in.
- They create, list, update, complete, and delete tasks.
- They get a feed of "your open tasks."
- They receive an email when assigned a task.
- Events flow to other services via Kafka.

By the capstone it has **17 features** (auth, persistence, caching, async
messaging, file uploads, observability, containerization). This module gives
you the empty shell they'll grow in.

---

## 2. Generating the project

The fastest, most reliable way to start a Spring Boot project is
**[start.spring.io](https://start.spring.io)**. Pick:

| Field | Value |
|-------|-------|
| Project | Maven |
| Language | Java |
| Spring Boot | 3.3.x (latest 3.3 at the time of writing) |
| Group | `com.taskforge` |
| Artifact | `taskforge` |
| Name | `taskforge` |
| Description | `Task tracker backend` |
| Package name | `com.taskforge` |
| Packaging | `Jar` |
| Java | `21` |

**Dependencies for this module** (add more in later modules):

- `Spring Web` — REST APIs and embedded Tomcat
- `Spring Boot Actuator` — health check, info, metrics (Module 15)

Click **Generate**, unzip, and put the contents at
`spring-boot-course/apps/taskforge/`.

> **CLI alternative:** `curl https://start.spring.io/starter.zip -d type=maven-project -d language=java -d bootVersion=3.3.4 -d groupId=com.taskforge -d artifactId=taskforge -d name=taskforge -d javaVersion=21 -d dependencies=web,actuator -o taskforge.zip && unzip taskforge.zip`

---

## 3. The project layout

```
taskforge/
├── pom.xml                         ← Maven build, dependencies, plugins
├── mvnw, mvnw.cmd                  ← Maven wrapper (Unix / Windows)
├── .gitignore
├── HELP.md
└── src/
    ├── main/
    │   ├── java/com/taskforge/
    │   │   └── TaskforgeApplication.java     ← main class
    │   └── resources/
    │       ├── application.yml                ← config (one file, all profiles)
    │       ├── application-dev.yml            ← dev overrides
    │       ├── application-prod.yml           ← prod overrides
    │       ├── static/                        ← served at / (if any)
    │       └── templates/                     ← Thymeleaf/HTML templates (we won't use)
    └── test/
        └── java/com/taskforge/
            └── TaskforgeApplicationTests.java
```

> **Conventions:** business code goes under `com.taskforge.<feature>.*` (e.g.
> `com.taskforge.task`, `com.taskforge.auth`). Tests live in
> `src/test/java/...` mirroring the package tree.

---

## 4. The main class

```java
package com.taskforge;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class TaskforgeApplication {
    public static void main(String[] args) {
        SpringApplication.run(TaskforgeApplication.class, args);
    }
}
```

`@SpringBootApplication` is a meta-annotation that combines:
- `@Configuration` — this class can declare beans.
- `@EnableAutoConfiguration` — turn on Boot's auto-config.
- `@ComponentScan` — scan the package and sub-packages for beans.

`SpringApplication.run(...)` is what boots the app: it creates the
`ApplicationContext` (Spring's IoC container), starts the embedded server,
and runs the app until you kill it.

---

## 5. The three ideas that make Spring Boot work

### 5.1 Starters

A **starter** is a curated set of dependencies that work together. Adding
`spring-boot-starter-web` brings in:

- `spring-web`, `spring-webmvc` (the web framework)
- `spring-boot-starter-tomcat` (embedded server)
- `spring-boot-starter-json` (Jackson)
- `spring-boot-starter-validation` (Hibernate Validator)
- … and the right versions of all of the above, managed by the parent POM.

You don't have to figure out version numbers. That's the whole point.

> **Mental model:** a starter is a **recipe**. The parent POM
> (`spring-boot-starter-parent`) is the **pantry** that knows which version
> of every ingredient goes with which starter.

The starters you'll use in this course are listed in the course README.

### 5.2 Auto-configuration

Spring Boot **looks at your classpath** and configures things automatically:

- Tomcat on the classpath → start an embedded Tomcat on port 8080.
- Jackson on the classpath → enable JSON serialization of return values.
- Spring Data JPA + a JDBC driver on the classpath → configure a `DataSource`.
- `spring-boot-starter-actuator` on the classpath → expose `/actuator/*`.

You can **override** any auto-configured bean by declaring your own. Spring
backs off automatically.

> **Example:** define your own `DataSource` bean → Spring stops trying to
> create one. No flag to flip.

### 5.3 The main application class

The class with `@SpringBootApplication` is the **root of the bean tree**:
- Component scanning starts from its package and goes deeper.
- Auto-configuration is enabled for the whole context.
- It's where you run from.

If you put `TaskforgeApplication` in `com.taskforge`, every bean must be in
`com.taskforge` or a sub-package. Otherwise Spring won't find it.

---

## 6. `application.yml` — your config file

`src/main/resources/application.yml` is the single config file Spring Boot
reads at startup:

```yaml
spring:
  application:
    name: taskforge
  datasource:
    url: jdbc:postgresql://localhost:5432/taskforge
    username: taskforge
    password: taskforge
  jpa:
    hibernate:
      ddl-auto: validate          # we manage schema with Flyway (Module 05)
    open-in-view: false           # anti-pattern — close sessions in the service
  data:
    redis:
      host: localhost
      port: 6379

server:
  port: 8080

management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
```

Properties in this file are bound to `@ConfigurationProperties` classes or
injected with `@Value("${...}")`. Module 09 goes deep on this.

---

## 7. The executable JAR

`mvn package` produces `target/taskforge-0.0.1-SNAPSHOT.jar` — a **fat JAR**
that contains your classes plus every dependency. You can run it with:

```bash
java -jar target/taskforge-0.0.1-SNAPSHOT.jar
```

The "magic" is the **Spring Boot Maven plugin**, which repackages the JAR so
its `main` class is the Boot launcher, and bundles everything inside. No
classpath headaches, no Tomcat install.

> **Docker tip (Module 14):** the fat JAR is exactly what your Docker image
> runs. `FROM eclipse-temurin:21-jre` + `COPY target/*.jar app.jar` +
> `ENTRYPOINT ["java","-jar","/app.jar"]` is a complete, runnable image.

---

## 8. Your first health check

`spring-boot-starter-actuator` gives you `/actuator/health` for free:

```bash
mvn spring-boot:run
curl -s localhost:8080/actuator/health
# → {"status":"UP"}
```

This single endpoint is what Docker, Kubernetes, and load balancers will
probe in Modules 14–15. "UP" means "send me traffic."

---

## 9. How a request flows through the app (preview)

```
HTTP GET /tasks
     │
     ▼
Tomcat (embedded)             ← spring-boot-starter-tomcat
     │
     ▼
DispatcherServlet             ← Spring MVC's front controller
     │   matches /tasks to TaskController#getAllTasks()
     ▼
TaskController#getAllTasks()  ← @RestController, @GetMapping
     │
     ▼
TaskService#listAll()         ← @Service (Module 03)
     │
     ▼
TaskRepository#findAll()      ← Spring Data (Module 05)
     │
     ▼
Postgres                        ← DataSource (HikariCP)
     │
     ▼
response ← Jackson serializes List<Task> → JSON
     │
     ▼
HTTP 200 + application/json
```

You haven't written all of these layers yet. By Module 05 you will.

---

## 10. Do the lab

Generate the project, run it, and confirm the basics work. You'll keep this
project for every later module.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

Spring Boot · starter · auto-configuration · `@SpringBootApplication` · `ApplicationContext` · embedded server · `application.yml` · fat JAR · Actuator

**Next →** [Module 03: Dependency Injection & Beans](../03-dependency-injection-beans/)

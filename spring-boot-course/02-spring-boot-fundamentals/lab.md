# Lab 02 — Generate, Run, and Understand a Spring Boot App

**You'll:** generate the `taskforge` project with `start.spring.io`, build it,
run it, hit its health endpoint, and inspect the auto-config report.

⏱️ ~40 min. The dev data services from Module 00 must be running.

---

## Part A — Generate the project

Use the CLI (or open <https://start.spring.io> in a browser):

```bash
cd spring-boot-course/apps
curl -G https://start.spring.io/starter.zip \
  -d type=maven-project \
  -d language=java \
  -d bootVersion=3.3.4 \
  -d groupId=com.taskforge \
  -d artifactId=taskforge \
  -d name=taskforge \
  -d description="Task tracker backend" \
  -d packageName=com.taskforge \
  -d packaging=jar \
  -d javaVersion=21 \
  -d dependencies=web,actuator \
  -o taskforge.zip
unzip taskforge.zip -d taskforge
cd taskforge
```

✅ **Checkpoint:** `taskforge/pom.xml` exists, `mvn -q -DskipTests package`
succeeds.

---

## Part B — Read the generated `pom.xml`

Open `pom.xml`. Note:

```xml
<parent>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-parent</artifactId>
  <version>3.3.4</version>
</parent>
```

The parent POM is what gives you **dependency management** for every Spring
library — you don't write version numbers in your `<dependency>` blocks.

```xml
<dependencies>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>   <!-- no version! -->
  </dependency>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
  </dependency>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <scope>test</scope>
  </dependency>
</dependencies>
```

✅ **Checkpoint:** you can name the two starters and the one test starter.

---

## Part C — Run it and prove it works

```bash
mvn spring-boot:run
```

You should see:
```
  .   ____          _            __ _ _
 /\\ / ___'_ __ _ _(_)_ __  __ _ \ \ \ \
( ( )\___ | '_ | '_| | '_ \/ _` | \ \ \ \
 \\/  ___)| |_)| | | | | || (_| |  ) ) ) )
  '  |____| .__|_| |_|_| |_\__, | / / / /
 =========|_|==============|___/=/_/_/_/

:: Spring Boot ::                (v3.3.4)

... Tomcat started on port 8080 (http) with context path ''
... Started TaskforgeApplication in 1.234 seconds
```

In another terminal:
```bash
curl -s localhost:8080/actuator/health
# → {"status":"UP"}
```

Stop the app with `Ctrl-C`.

---

## Part D — Enable the auto-config report

The **auto-configuration report** tells you exactly what Spring Boot did at
startup, and why. Enable it:

`src/main/resources/application.yml`:
```yaml
debug: true
```

Run again and look for the report in the console:
```
CONDITIONS EVALUATION REPORT
Positive matches:
-----------------
   AopAutoConfiguration matched:
      - @ConditionalOnProperty (spring.aop.auto=true) matched

   DispatcherServletAutoConfiguration matched:
      - @ConditionalOnClass (…DispatcherServlet) found on classpath

Negative matches:
-----------------
   ActiveMQAutoConfiguration:
      - @ConditionalOnClass did not find required class 'javax.jms.ConnectionFactory'
```

> **Read this for the first time and you'll see:** Spring Boot only turned on
> the things you have libraries for. No `ConnectionFactory` on the classpath →
> no `ActiveMQAutoConfiguration`. Add a starter, get the config.

✅ **Checkpoint:** the report shows positive matches for `WebMvcAutoConfiguration`,
`JacksonAutoConfiguration`, and `ManagementContextAutoConfiguration`.

---

## Part E — Add a `HelloController` so you can see the web layer work

Create `src/main/java/com/taskforge/hello/HelloController.java`:

```java
package com.taskforge.hello;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.Map;

@RestController
public class HelloController {

    @GetMapping("/")
    public Map<String, Object> hello() {
        return Map.of(
            "service", "taskforge",
            "status",  "ok",
            "time",    Instant.now().toString()
        );
    }

    @GetMapping("/hello/{name}")
    public Map<String, String> greet(String name) {
        return Map.of("message", "Hello, " + name + "!");
    }
}
```

> Wait — `greet(String name)` has no `@PathVariable`. Spring binds
> path/template variables AND request parameters to method parameters by
> name. Add `?name=ann` and you see the query-param binding; remove it and
> Spring uses the path. Module 04 is the deep dive.

Run again and try:
```bash
curl -s localhost:8080/
curl -s localhost:8080/hello/ann
curl -s 'localhost:8080/hello/ann?name=override'
```

✅ **Checkpoint:** the root returns a JSON map, `/hello/ann` returns a
greeting, and the `?name=...` query parameter overrides the path variable.

---

## What you learned

- A Spring Boot project is generated from `start.spring.io` with the right
  starters and a version-managed parent POM.
- `@SpringBootApplication` is the root of the bean tree.
- Auto-configuration enables features based on what's on the classpath.
- `mvn spring-boot:run` starts the embedded server on port 8080.
- `/actuator/health` works for free and is your future Docker/K8s probe.
- A `@RestController` returns JSON by default; Spring binds path variables
  and query parameters to method parameters by name.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 03](../03-dependency-injection-beans/).

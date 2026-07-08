# Challenge 02 — Reference Solution

### 1. The parent
> The parent is `org.springframework.boot:spring-boot-starter-parent:3.3.4`.
> It provides **dependency management** — every Spring Boot library has a
> version already pinned, so you never write `<version>` in your
> `<dependency>` blocks.

### 2. Transitive deps
```bash
mvn -q dependency:tree | head -30
```
You'll see:
```
[INFO] +- org.springframework.boot:spring-boot-starter-web:jar:3.3.4
[INFO] |  +- org.springframework.boot:spring-boot-starter-json:jar:3.3.4
[INFO] |  |  +- com.fasterxml.jackson.core:jackson-databind:jar:2.17.2
[INFO] |  |  +- com.fasterxml.jackson.datatype:jackson-datatype-jdk8:jar:2.17.2
[INFO] |  +- org.springframework.boot:spring-boot-starter-tomcat:jar:3.3.4
[INFO] |  |  +- org.apache.tomcat.embed:tomcat-embed-core:jar:10.1.30
[INFO] |  +- org.springframework:spring-web:jar:6.1.13
```
The deepest leaves are Jackson and Tomcat's embedded core.

### 3. Negative matches
For example, with no JPA starter yet:
```
   JpaRepositoriesAutoConfiguration:
     - @ConditionalOnClass did not find required class 'org.springframework.data.jpa.repository.JpaRepository'
```
…and with no Redis starter:
```
   RedisAutoConfiguration:
     - @ConditionalOnClass did not find required class 'org.springframework.data.redis.core.RedisOperations'
```
> Spring doesn't configure things it can't find the libraries for.

### 4. Change the port
```yaml
# src/main/resources/application.yml
server:
  port: 9090
```
Restart and `curl localhost:9090/actuator/health` returns `UP`. Port is
back to 8080 for the rest of the course.

### 5. Info endpoint
`application.yml`:
```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info
info:
  app:
    name: ${spring.application.name}
    version: 0.0.1-SNAPSHOT
```
`curl localhost:8080/actuator/info` →
```json
{"app":{"name":"taskforge","version":"0.0.1-SNAPSHOT"}}
```

### 6. Disable Tomcat
```yaml
spring:
  main:
    web-application-type: none     # or: servlet
```
Restart — the app starts, but no port is bound, no web server starts, and
`/actuator/health` is unreachable. Set it back to `servlet` (or remove the
line) for the rest of the course.

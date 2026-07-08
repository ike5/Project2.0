# Challenge 02 — Spring Boot Internals

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Find the parent.** In `pom.xml`, what is the parent POM and what version?
   What does it give you for free (one sentence)?

2. **List the starters in your JAR.** Run `mvn -q dependency:tree | head -30`
   and identify the three direct dependencies that `spring-boot-starter-web`
   pulled in transitively. What is the deepest dependency you can see?

3. **The condition.** With `debug: true` still on, look at the auto-config
   report. Find **two negative matches** (configs that were NOT applied) and
   explain in one sentence each *why* they didn't match.

4. **Change a property.** Set `server.port: 9090` in `application.yml`,
   restart, and confirm the app now starts on `9090`. (Reset it back to 8080
   after.)

5. **Add an info endpoint.** `management.info.env.enabled=true` lets you
   inject info from env vars. Add:
   ```yaml
   info:
     app:
       name: ${spring.application.name}
       version: 0.0.1-SNAPSHOT
   ```
   Hit `/actuator/info` and report what you see. (You'll need to also expose
   the `info` endpoint.)

6. **Stretch:** Disable the embedded Tomcat in `application.yml` and prove
   the app no longer starts a web server. Then re-enable it. What's the
   property?

## Success criteria

- [ ] You can name the parent POM and what it provides.
- [ ] You can list transitive deps from `spring-boot-starter-web`.
- [ ] You can read the auto-config report and explain a positive and a
  negative match.
- [ ] You changed the port and confirmed the app moved.
- [ ] `/actuator/info` returns your app's metadata.
- [ ] Stretch: you can disable and re-enable the embedded server.

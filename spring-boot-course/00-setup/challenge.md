# Challenge 00 — Know Your Tools

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Create a table by hand.** Using `psql` in the Postgres container, create a
   throwaway table `ping (id serial primary key, note text)`, insert one row,
   and `SELECT *` it back. Then `DROP` it.

2. **Make Redis forget.** Set a key `flash` to any value with a **10-second**
   expiry in a single command, immediately read it, wait 11 seconds, and confirm
   it's gone (`GET` returns `(nil)`).

3. **Kafka round-trip.** Use `kafka-console-producer` to send 3 messages to a
   topic `greet`, then start a `kafka-console-consumer` with `--from-beginning`
   and confirm all 3 arrive in order.

4. **MailHog + MinIO.** Open the MailHog inbox and the MinIO console. In one
   sentence each, say what each is for in this course.

5. **Spring Boot startup time.** Run the Hello app with `mvn spring-boot:run`
   and report: the banner line, the port it started on, and how long startup
   took (printed at the end: `Started HelloSpringApplication in X.XXX seconds`).

6. **Stretch:** Explain in two sentences why Spring Boot includes an
   *embedded* web server instead of expecting you to deploy a WAR to an
   external Tomcat.

## Success criteria

- [ ] You created, queried, and dropped a table in the `taskforge` database.
- [ ] A Redis key with a 10s TTL expired on its own.
- [ ] Three Kafka messages produced → consumed in order.
- [ ] You can state what MailHog and MinIO are used for.
- [ ] You can read the Spring Boot startup banner and report the startup time.
- [ ] You can explain the embedded-server design choice.

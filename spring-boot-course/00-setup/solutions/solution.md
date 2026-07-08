# Challenge 00 — Reference Solution

### 1. Create a table by hand
```bash
docker compose -f compose.dev.yml exec postgres psql -U taskforge -d taskforge
```
```sql
CREATE TABLE ping (id serial primary key, note text);
INSERT INTO ping (note) VALUES ('hello');
SELECT * FROM ping;       -- 1 | hello
DROP TABLE ping;
\q
```

### 2. Make Redis forget
```bash
docker compose -f compose.dev.yml exec redis redis-cli
```
```
SET flash hi EX 10     -> OK     # EX 10 sets a 10-second TTL in one command
GET flash              -> "hi"
# wait 11 seconds…
GET flash              -> (nil)  # the key expired and was removed
```

### 3. Kafka round-trip
```bash
# producer (type 3 lines, then Ctrl-C)
docker compose -f compose.dev.yml exec kafka \
  kafka-console-producer.sh --bootstrap-server localhost:9092 --topic greet
> hi
> hello
> bye
```
```bash
# consumer (reads from the beginning)
docker compose -f compose.dev.yml exec kafka \
  kafka-console-consumer.sh --bootstrap-server localhost:9092 \
  --topic greet --from-beginning
hi
hello
bye
```

### 4. MailHog + MinIO
- **MailHog** is a fake SMTP server with a web inbox — Module 12 uses it to
  see transactional emails your app sends during development.
- **MinIO** is an S3-compatible object store — Module 12 uses it to store
  file attachments without needing AWS.

### 5. Spring Boot startup
```
  .   ____          _            __ _ _
 /\\ / ___'_ __ _ _(_)_ __  __ _ \ \ \ \
( ( )\___ | '_ | '_| | '_ \/ _` | \ \ \ \
 \\/  ___)| |_)| | | | | || (_| |  ) ) ) )
  '  |____| .__|_| |_|_| |_\__, | / / / /
 =========|_|==============|___/=/_/_/_/

:: Spring Boot ::                (v3.3.4)

... Tomcat started on port 8080 (http) ...
Started HelloSpringApplication in 1.234 seconds
```

### 6. Embedded server
> An embedded server means the JAR you ship *is* the runtime — no separate
> Tomcat install, no WAR layout, no classpath conflicts. You get a single
> `java -jar app.jar` that runs identically on a laptop, a CI box, and a
> container, which is what makes "build once, deploy anywhere" actually true.

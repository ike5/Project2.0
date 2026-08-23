# VERIFY — Confirm Your Environment

Run this **after Module 00** and before Module 01. It takes ~15 minutes and
proves every tool the course depends on actually works on your machine.

If any step fails, fix it now. Debugging your toolchain in Module 18 while three
Redis nodes are mid-failover is not the experience we're going for.

---

## 0. Resource budget

The heavy modules (18, 19, 22) run a lot of containers. Check you have room:

```bash
free -g 2>/dev/null || vm_stat | head -3   # Linux || macOS
docker system df
df -h .
```

**Expected:** at least **16 GB total RAM** (12 GB works with the low-memory path
in Module 00), and **40 GB free disk**.

| Phase | Containers | Approx RAM |
|-------|-----------|-----------|
| 0–1 | postgres, redis | ~1 GB |
| 2 | + redis-2, 2× app | ~2.5 GB |
| 3 | + replica, pgbouncer | ~3.5 GB |
| 4 | + kafka, zookeeper-less KRaft | ~5 GB |
| 5 (Compose HA) | 3× redis + 3× sentinel, 3× patroni, etcd, haproxy, 3× app, nginx | ~9 GB |
| 5 (k8s) | kind, 3 nodes | ~10 GB |

---

## 1. Java 21

```bash
java --version
```

**Expected:** version `21.x` or newer.
```
openjdk 21.0.5 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
```

Now prove **virtual threads** actually work — this is the feature the whole
course leans on:

```bash
cat > /tmp/VT.java <<'EOF'
public class VT {
  public static void main(String[] a) throws Exception {
    var t = Thread.ofVirtual().unstarted(() ->
        System.out.println("virtual=" + Thread.currentThread().isVirtual()));
    t.start(); t.join();
  }
}
EOF
java /tmp/VT.java
```

**Expected:**
```
virtual=true
```

✅ If you see `virtual=true`, your JDK is correct. If `java` reports 17 or
earlier, go back to Module 00 — this course does not work on Java 17.

---

## 2. Maven

```bash
mvn -version
```

**Expected:** `Apache Maven 3.9.x` or newer, and the Java version line must show
your **21** JDK, not a different one:
```
Apache Maven 3.9.9
Java version: 21.0.5, vendor: Eclipse Adoptium
```

⚠️ A common trap: Maven picking up an older `JAVA_HOME` than your shell's
`java`. If the two disagree, fix `JAVA_HOME` before continuing.

---

## 3. Docker and Compose v2

```bash
docker --version
docker compose version
docker run --rm hello-world | head -2
```

**Expected:**
```
Docker version 27.x.x, build ...
Docker Compose version v2.29.x
Hello from Docker!
```

Note: `docker compose` (space), not `docker-compose` (hyphen). Compose v1 is
end-of-life and several files in this course use v2-only syntax.

---

## 4. Redis 7

```bash
docker run -d --name verify-redis -p 6379:6379 redis:7-alpine
docker exec verify-redis redis-cli PING
docker exec verify-redis redis-cli INFO server | grep redis_version
```

**Expected:**
```
PONG
redis_version:7.4.1
```

Prove **Streams** exist (Module 09 depends on them) and **RESP3** is available:

```bash
docker exec verify-redis redis-cli XADD verify '*' hello world
docker exec verify-redis redis-cli XLEN verify
docker exec verify-redis redis-cli -3 HELLO 3 | head -4
```

**Expected:** an ID like `1735689600000-0`, then:
```
(integer) 1
```
and a `HELLO 3` reply listing `proto` → `3`.

Clean up:
```bash
docker rm -f verify-redis
```

---

## 5. Postgres 16

```bash
docker run -d --name verify-pg -e POSTGRES_PASSWORD=pulse -p 5432:5432 postgres:16-alpine
sleep 5
docker exec verify-pg psql -U postgres -c "SELECT version();"
```

**Expected:** a line beginning
```
 PostgreSQL 16.x on x86_64-pc-linux-gnu ...
```

Prove **declarative partitioning** works (Module 13 depends on it):

```bash
docker exec verify-pg psql -U postgres -c "
CREATE TABLE t (id bigint, created_at timestamptz) PARTITION BY RANGE (created_at);
CREATE TABLE t_2026_01 PARTITION OF t FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
INSERT INTO t VALUES (1, '2026-01-15');
SELECT tableoid::regclass AS partition, id FROM t;"
```

**Expected:**
```
 partition | id
-----------+----
 t_2026_01 |  1
```

✅ The row landed in the child table, not the parent. That's partition routing
working.

Clean up:
```bash
docker rm -f verify-pg
```

---

## 6. k6 (WebSocket load testing)

```bash
k6 version
```

**Expected:** `k6 v0.5x.x` or newer.

Prove the WebSocket module is present:

```bash
cat > /tmp/ws-check.js <<'EOF'
import ws from 'k6/ws';
import { check } from 'k6';
export default function () {
  const res = ws.connect('wss://echo.websocket.org', {}, function (socket) {
    socket.on('open', () => { socket.send('ping'); });
    socket.on('message', (m) => { console.log('got: ' + m); socket.close(); });
    socket.setTimeout(() => socket.close(), 3000);
  });
  check(res, { 'handshake was 101': (r) => r && r.status === 101 });
}
EOF
k6 run --vus 1 --iterations 1 /tmp/ws-check.js
```

**Expected:** a summary containing
```
✓ handshake was 101
```

⚠️ If you're offline or behind a proxy that blocks the public echo server, this
step will fail on the *network*, not on k6. Module 06 runs everything against
your own local server, so a k6 version output alone is sufficient to proceed.

---

## 7. Node 20+ (for the Next.js client in Module 17)

```bash
node --version
npm --version
```

**Expected:** `v20.x` or newer, npm `10.x` or newer.

---

## 8. `websocat` (manual socket poking)

Used throughout for talking to your server by hand.

```bash
websocat --version
```

**Expected:** `websocat 1.13.x` or similar. Module 00 covers installation; if
you'd rather not install it, every `websocat` step has a `wscat` (npm) or browser
console alternative noted in the lab.

---

## 9. End-to-end smoke test

This starts the whole Phase-1 data tier and confirms the pieces talk to each
other.

```bash
cd spring-boot-chat-course/infra
docker compose -f compose.dev.yml up -d
docker compose -f compose.dev.yml ps
```

**Expected:** both services `running (healthy)`:
```
NAME            IMAGE               STATUS
pulse-postgres  postgres:16-alpine  Up 20 seconds (healthy)
pulse-redis     redis:7-alpine      Up 20 seconds (healthy)
```

Confirm connectivity from your host:

```bash
docker exec pulse-redis redis-cli PING
docker exec pulse-postgres psql -U pulse -d pulse -c "SELECT 1 AS ok;"
```

**Expected:**
```
PONG
 ok
----
  1
```

Tear down when you're done verifying:

```bash
docker compose -f compose.dev.yml down -v
```

---

## Checklist

- [ ] `java --version` shows 21+ and `virtual=true` printed
- [ ] `mvn -version` reports the *same* Java 21 JDK
- [ ] `docker compose version` shows v2
- [ ] Redis 7 responds `PONG`, `XADD` works, `HELLO 3` returns proto 3
- [ ] Postgres 16 runs and routes a row into a partition
- [ ] `k6 version` works
- [ ] `node --version` shows 20+
- [ ] `websocat --version` works (or you've chosen an alternative)
- [ ] The dev Compose stack comes up healthy and both services answer

All checked? Go to **[Module 01 — Java 21 Concurrency for Real-Time](./01-java21-concurrency/)**.

---

## If something failed

See [`cheatsheets/troubleshooting.md`](./cheatsheets/troubleshooting.md) for
decision trees. The three most common problems:

| Symptom | Usual cause | Fix |
|---------|-------------|-----|
| `mvn` uses Java 17 but `java` is 21 | `JAVA_HOME` points elsewhere | `export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))` |
| `port is already allocated` | A stray container from a prior module | `docker ps -a`, then `docker rm -f <name>` |
| Postgres container exits immediately | Stale volume with a different password | `docker compose down -v` (note the `-v`) |

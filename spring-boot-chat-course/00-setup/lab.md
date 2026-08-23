# Lab 00 — Install the Toolchain

**You'll:** install Java 21, Maven, Docker, k6, Node and websocat; start the dev
data tier; create the project skeleton; and record your machine's baseline.

⏱️ ~60 min. Run from the repo root unless a step says otherwise.

---

## Part A — Java 21

Java 21 is non-negotiable for this course. Virtual threads are the foundation of
Phase 1.

### macOS
```bash
brew install --cask temurin@21
/usr/libexec/java_home -V
export JAVA_HOME=$(/usr/libexec/java_home -v 21)
```

### Linux (SDKMAN — recommended, keeps versions side by side)
```bash
curl -s "https://get.sdkman.io" | bash
source "$HOME/.sdkman/bin/sdkman-init.sh"
sdk install java 21.0.5-tem
sdk use java 21.0.5-tem
```

### Linux (distro packages)
```bash
# Debian/Ubuntu
sudo apt update && sudo apt install -y openjdk-21-jdk
# Fedora/RHEL
sudo dnf install -y java-21-openjdk-devel
```

Confirm:
```bash
java --version
echo $JAVA_HOME
```

**Expected:**
```
openjdk 21.0.5 2024-10-15 LTS
OpenJDK Runtime Environment Temurin-21.0.5+11 (build 21.0.5+11-LTS)
OpenJDK 64-Bit Server VM Temurin-21.0.5+11 (build 21.0.5+11-LTS, mixed mode, sharing)
```

Now prove virtual threads work — this is the feature everything else rests on:

```bash
mkdir -p /tmp/vtcheck && cat > /tmp/vtcheck/VT.java <<'EOF'
public class VT {
    public static void main(String[] args) throws Exception {
        Thread t = Thread.ofVirtual().unstarted(() ->
            System.out.println("isVirtual=" + Thread.currentThread().isVirtual()
                             + " name=" + Thread.currentThread()));
        t.start();
        t.join();
    }
}
EOF
java /tmp/vtcheck/VT.java
```

**Expected:**
```
isVirtual=true name=VirtualThread[#21]/runnable@ForkJoinPool-1-worker-1
```

✅ Note the `ForkJoinPool-1-worker-1` at the end — that's the **carrier thread**
your virtual thread is mounted on. You'll meet that term properly in Module 01.

---

## Part B — Maven

```bash
# macOS
brew install maven
# Linux via SDKMAN
sdk install maven
# Debian/Ubuntu
sudo apt install -y maven
```

```bash
mvn -version
```

**Expected** — and check the `Java version` line carefully:
```
Apache Maven 3.9.9
Maven home: /usr/share/maven
Java version: 21.0.5, vendor: Eclipse Adoptium, runtime: /usr/lib/jvm/temurin-21
```

⚠️ **The single most common setup problem in this course:** `java --version` says
21 but `mvn -version` says 17, because Maven reads `JAVA_HOME` and your shell
reads `PATH`. If they disagree:

```bash
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
# persist it in ~/.zshrc or ~/.bashrc
```

---

## Part C — Docker & Compose v2

### macOS
```bash
brew install --cask docker    # then launch Docker Desktop once
```
In Docker Desktop → Settings → Resources, give it at least **8 GB RAM** (12 GB
if you plan to do Module 19's kind cluster). macOS runs containers in a VM, so
this limit is real and separate from your machine's RAM.

### Linux
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
newgrp docker                  # or log out and back in
```

Confirm:
```bash
docker --version
docker compose version
docker run --rm hello-world | head -3
```

**Expected:**
```
Docker version 27.3.1, build ce12230
Docker Compose version v2.29.7

Hello from Docker!
```

⚠️ `docker compose` (space) not `docker-compose` (hyphen). Compose v1 is EOL and
several files in this course use v2-only syntax such as top-level `name:`.

---

## Part D — k6

```bash
# macOS
brew install k6

# Debian/Ubuntu
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
     --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" \
     | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt update && sudo apt install -y k6

# Fedora/RHEL
sudo dnf install -y https://dl.k6.io/rpm/repo.rpm && sudo dnf install -y k6
```

```bash
k6 version
```

**Expected:**
```
k6 v0.54.0 (go1.23.2, linux/amd64)
```

---

## Part E — Node 20+, websocat, jq

```bash
# Node via nvm (recommended — Module 17 needs 20+)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.nvm/nvm.sh
nvm install 20 && nvm use 20

# websocat
brew install websocat                                    # macOS
cargo install websocat                                   # any platform with Rust
# or grab a static binary from github.com/vi/websocat/releases

# jq
brew install jq          # macOS
sudo apt install -y jq   # Debian/Ubuntu
```

```bash
node --version && npm --version && websocat --version && jq --version
```

**Expected:**
```
v20.18.0
10.8.2
websocat 1.13.0
jq-1.7.1
```

> **No websocat?** Every lab step using it has an alternative noted. The easiest
> is `npm i -g wscat` (`wscat -c ws://localhost:8080/ws`).

---

## Part F — Start the dev data tier

```bash
cd spring-boot-chat-course/infra
docker compose -f compose.dev.yml up -d
docker compose -f compose.dev.yml ps
```

**Expected** — both `(healthy)`, which may take ~15 seconds:
```
NAME             IMAGE                STATUS                   PORTS
pulse-postgres   postgres:16-alpine   Up 18 seconds (healthy)  0.0.0.0:5432->5432/tcp
pulse-redis      redis:7-alpine       Up 18 seconds (healthy)  0.0.0.0:6379->6379/tcp
```

If a container shows `(health: starting)` for more than a minute, check
`docker compose -f compose.dev.yml logs postgres`.

Confirm both actually answer:

```bash
docker exec pulse-redis redis-cli PING
docker exec pulse-postgres psql -U pulse -d pulse -c "SELECT version();" | head -3
```

**Expected:**
```
PONG
                                                 version
---------------------------------------------------------------------------------------------------------
 PostgreSQL 16.4 on x86_64-pc-linux-musl, compiled by gcc (Alpine 13.2.1_git20240309) 13.2.1 20240309, 64-bit
```

### Why these settings?

Open `compose.dev.yml` and read the `command:` blocks. Two choices worth noting
now, because you'll revisit both:

- **`--maxmemory-policy noeviction`** on Redis. The default (`noeviction`) means
  Redis returns an *error* when full rather than silently discarding keys. For a
  cache you'd want `allkeys-lru`; for a message backbone, silent data loss is
  the worst possible failure mode. Module 08 argues this properly.
- **`log_min_duration_statement=200`** on Postgres. Anything slower than 200 ms
  lands in the log. In Module 12 you'll watch a query cross that line and learn
  why.

---

## Part G — Create the project skeleton

You'll generate the real Spring Boot project in Module 02. For now, just make
the directory and start your results file.

```bash
cd /path/to/Project2.0/spring-boot-chat-course
mkdir -p apps
```

Create `results.md` at the course root — **this file matters**. Modules 06, 09,
15, 16, 18 and 22 all compare against numbers you record here.

```bash
cat > results.md <<'EOF'
# Pulse — Benchmark Log

Every measured number in this course lands here. Always record the context:
machine, JDK, workload shape, and duration. A number without context is noise.

## Machine

- CPU:
- RAM:
- OS:
- JDK:
- Docker RAM limit (macOS only):

## Baseline (Module 00)

- Process FD limit (`ulimit -n`):
- System FD limit (`/proc/sys/fs/file-max`):
- Ephemeral port range:
- Bytes per platform thread:
- Bytes per virtual thread:
- Idle container RSS — postgres / redis:

## Module 06 — Single-node ceiling

- Max stable connections:
- Bytes per connection (heap after GC / conns):
- p50 / p95 / p99 fan-out latency at that load:
- What broke first:

## Module 09 — Pub/Sub vs Streams

## Module 15 — Virtual threads vs WebFlux

## Module 16 — Redis vs Kafka

## Module 18 — Failover cost

## Module 22 — Capstone target
EOF
```

Fill in the **Machine** section now:

```bash
{
  echo "nproc: $(nproc 2>/dev/null || sysctl -n hw.ncpu)"
  echo "ram:   $(free -h 2>/dev/null | awk '/Mem:/{print $2}' || echo "$(($(sysctl -n hw.memsize)/1073741824))Gi")"
  echo "os:    $(uname -sr)"
  echo "jdk:   $(java --version | head -1)"
} 
```

**Expected** (yours will differ — that's the point):
```
nproc: 8
ram:   15Gi
os:    Linux 6.8.0-45-generic
jdk:   openjdk 21.0.5 2024-10-15 LTS
```

Paste those into `results.md`.

---

## Part H — Record your connection limits

These three numbers determine your hard ceiling before any code runs.

```bash
ulimit -n                             # this process
cat /proc/sys/fs/file-max 2>/dev/null || sysctl -n kern.maxfiles   # whole system
cat /proc/sys/net/ipv4/ip_local_port_range 2>/dev/null || sysctl -n net.inet.ip.portrange.first
```

**Expected** (typical Linux defaults):
```
1024
9223372036854775807
32768	60999
```

That `1024` is almost certainly what will bind first, and it's the reason
"my server stops accepting connections at exactly 1016 clients" is such a
common confused bug report. Raise it for your shell:

```bash
ulimit -n 100000
ulimit -n
```

**Expected:**
```
100000
```

> This only affects the current shell. Module 06 shows how to set it
> persistently and inside containers. For now, just know the number exists.

The ephemeral port range (`32768–60999` ≈ 28,000 ports) limits how many
*outbound* connections one machine can make to one destination. It constrains
your **load generator**, not your server — a distinction that has fooled a great
many people into thinking their server caps out at 28k. Module 06 revisits this.

Record all three in `results.md`.

---

## Part I — Run VERIFY

```bash
cd spring-boot-chat-course
# work through VERIFY.md end to end
```

Every box must be checked before Module 01.

---

## Cleanup

Leave the dev stack running if you're going straight to Module 01. Otherwise:

```bash
cd spring-boot-chat-course/infra
docker compose -f compose.dev.yml down
# add -v to also drop the volumes (a clean slate for next time)
```

---

## What you did

- Installed a Java 21 JDK and **proved virtual threads work** on it.
- Aligned `JAVA_HOME` with your shell's `java` (the classic trap).
- Brought up Postgres 16 and Redis 7 with settings chosen deliberately, not by
  default.
- Recorded the three limits that cap connection count, and learned which one
  binds first.
- Started `results.md`, which the rest of the course writes into.

Now do [`challenge.md`](./challenge.md) — it establishes the baseline numbers
that Module 06 will compare against.

Then: [Module 01 — Java 21 Concurrency for Real-Time](../01-java21-concurrency/).

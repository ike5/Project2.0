# Solutions — Module 00

Numbers below are from a reference machine: **8-core / 16 GB, Ubuntu 24.04,
Temurin 21.0.5**. Yours will differ. The *ratios* and the *ordering* are what
matter.

---

## Task 1 — Your hard connection ceiling

```bash
ulimit -n                                   # per-process soft limit
ulimit -Hn                                  # per-process hard limit
cat /proc/sys/fs/file-max                   # system-wide
cat /proc/sys/net/ipv4/ip_local_port_range  # ephemeral range
```

Reference output:
```
1024
1048576
9223372036854775807
32768	60999
```

| Limit | Value | Binds? |
|-------|-------|--------|
| Process FD soft limit | 1,024 | ✅ **This one binds first** |
| Process FD hard limit | 1,048,576 | No (raise the soft limit up to this freely) |
| System-wide FDs | ~9.2×10¹⁸ | No — effectively unbounded |
| Ephemeral ports | 28,232 | Not on the server side (see below) |

**Why the ephemeral range doesn't limit your server:**

A TCP connection is identified by the 4-tuple
`(src_ip, src_port, dst_ip, dst_port)`. The *server* keeps one listening port —
`:8080` — for every connection; only the client's port varies. So the server's
theoretical limit is `clients × 65535` distinct tuples, i.e. bounded by FDs and
memory, not ports.

The **client** is the constrained side: one machine making connections to one
`server_ip:8080` can only use its ~28k ephemeral ports. This is why Module 06
warns that your load generator plateaus around 28k and it isn't your server's
fault.

Fixes on the generator side: widen the range (`ip_local_port_range="10000 65535"`
→ ~55k), add source IPs, or use more generator hosts.

---

## Task 2 — Thread cost

```java
// ThreadCost.java  —  run: java ThreadCost.java platform 10000
public class ThreadCost {
    public static void main(String[] args) throws Exception {
        String kind = args[0];
        int n = Integer.parseInt(args[1]);
        var latch = new java.util.concurrent.CountDownLatch(1);

        long before = rss();
        var threads = new java.util.ArrayList<Thread>(n);
        for (int i = 0; i < n; i++) {
            Runnable r = () -> { try { latch.await(); } catch (Exception ignored) {} };
            Thread t = kind.equals("virtual")
                ? Thread.ofVirtual().unstarted(r)
                : Thread.ofPlatform().unstarted(r);
            t.start();
            threads.add(t);
        }
        Thread.sleep(3000);                       // let them all park
        long after = rss();
        System.out.printf("%s n=%d  rss_delta=%d KB  per_thread=%.1f KB%n",
                kind, n, after - before, (after - before) / (double) n);
        latch.countDown();
        for (Thread t : threads) t.join();
    }

    static long rss() throws Exception {          // Linux: VmRSS in KB
        for (String line : java.nio.file.Files.readAllLines(
                java.nio.file.Path.of("/proc/self/status"))) {
            if (line.startsWith("VmRSS:"))
                return Long.parseLong(line.replaceAll("\\D+", ""));
        }
        return -1;
    }
}
```

Reference results:

| Kind | N | RSS delta | Per thread |
|------|---|-----------|------------|
| platform | 1,000 | ~68 MB | **~68 KB** |
| platform | 10,000 | ~690 MB | **~69 KB** |
| platform | 1,000,000 | ❌ `OutOfMemoryError: unable to create native thread` at ~32,000 | — |
| virtual | 10,000 | ~11 MB | **~1.1 KB** |
| virtual | 1,000,000 | ~830 MB | **~0.85 KB** |

**Reading these numbers correctly:**

- The famous "1 MB per thread" is the *reserved virtual address space* for the
  stack (`-Xss`, default 1 MB on 64-bit Linux). RSS is what's actually **touched**
  — ~68 KB for a thread that parks immediately. The 1 MB figure isn't wrong, it's
  measuring a different thing: virtual memory, which is why `ps` shows a scary
  VSZ and a reasonable RSS.
- **The real platform-thread limit is usually not memory** — it's
  `/proc/sys/kernel/threads-max`, the `nproc` ulimit, or `vm.max_map_count`
  (each thread stack needs a memory mapping). On the reference machine the JVM
  died at ~32,000 threads, well before RAM ran out. Record whichever error you
  get; the failure mode is the lesson.
- Virtual threads are ~**60–80× cheaper** in RSS and, crucially, don't consume a
  kernel thread at all. A million of them fit in under a gigabyte.

> **This ratio is the entire argument of Module 01.** Write it in `results.md`.

---

## Task 3 — Docker overhead

```bash
docker compose -f infra/compose.dev.yml up -d
sleep 300
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}"
```

Reference:
```
NAME             MEM USAGE / LIMIT   CPU %
pulse-postgres   38.4MiB / 15.5GiB   0.02%
pulse-redis      9.8MiB / 15.5GiB    0.15%
```

Idle cost is trivial — **~50 MB for both**. Worth knowing so that when Module 18
runs 15 containers, you can tell the difference between "baseline overhead" and
"something is actually using memory."

Redis's 0.15% idle CPU is its `serverCron` housekeeping (expiry sampling, etc.),
not a problem.

---

## Task 4 — Fan-out amplification

**Given:** 10,000 users, 1 message per user per 5 minutes.

Inbound is independent of room size:
```
10,000 users / 300 s = 33.3 messages/second inbound
```

**Rooms of 50** (49 other recipients per message):
```
outbound = 33.3 × 49 = 1,632 messages/second
amplification = 49×
```

**Rooms of 500** (499 other recipients):
```
outbound = 33.3 × 499 = 16,617 messages/second
amplification = 499×
```

**The asymmetry, in one sentence:**

> Inbound load is set by how many people *type*; outbound load is set by how many
> people *listen* — so growing room size multiplies your real work without
> changing the number that most dashboards display.

Corollaries worth internalizing:

- A capacity plan stated in "messages per second" is meaningless without the
  average room size. Always ask.
- The dangerous growth curve isn't user count — it's **room size**. Ten thousand
  users in 2-person DMs is a trivially small system. The same ten thousand in one
  `#general` is a hard one.
- This is why large systems cap room size, or switch strategy above a threshold
  (Module 13): below N members, fan out eagerly; above it, let clients pull.

---

## Task 5 (stretch) — Cost of an idle socket

Server:
```java
// IdleServer.java
import java.net.*; import java.util.*;
public class IdleServer {
    public static void main(String[] a) throws Exception {
        var keep = new ArrayList<Socket>();
        var ss = new ServerSocket(9099, 65535);
        System.out.println("pid=" + ProcessHandle.current().pid());
        while (true) {
            keep.add(ss.accept());
            if (keep.size() % 1000 == 0) System.out.println(keep.size());
        }
    }
}
```

Client:
```java
// IdleClient.java
import java.net.*; import java.util.*;
public class IdleClient {
    public static void main(String[] a) throws Exception {
        var keep = new ArrayList<Socket>();
        System.out.println("pid=" + ProcessHandle.current().pid());
        for (int i = 0; i < 10_000; i++) keep.add(new Socket("127.0.0.1", 9099));
        System.out.println("connected " + keep.size());
        Thread.sleep(600_000);
    }
}
```

```bash
ulimit -n 100000
java IdleServer.java &
java IdleClient.java &
sleep 30
grep VmRSS /proc/<server_pid>/status
grep VmRSS /proc/<client_pid>/status
cat /proc/net/sockstat
```

Reference:
```
server VmRSS:   215432 kB    (baseline JVM was ~48000 kB)
client VmRSS:   198760 kB
sockets: used 20114
TCP: inuse 20008 orphan 0 tw 12 alloc 20016 mem 1243
```

```
server delta = 215432 - 48000 = 167,432 KB over 10,000 sockets
             ≈ 16.7 KB per connection (userspace)
```

Plus kernel memory: `TCP ... mem 1243` counts **pages** (4 KB each) = ~5 MB of
socket buffers currently allocated — but that's for *idle* sockets. Linux grows
buffers on demand from `net.ipv4.tcp_rmem` / `tcp_wmem` (typical: 4 KB min,
~6 MB max **each way**). An active socket easily reaches 64 KB+ of kernel buffer.

**Bottom line: ~16 KB userspace + 8–64 KB kernel per connection, before Spring
exists.** So a bare-metal ceiling of ~50,000 connections costs roughly 1–4 GB in
sockets alone. When Module 06 measures 150 KB/connection for the real
application, you'll know that ~25 KB of it was never yours to optimize.

---

## Filling in `results.md`

```markdown
## Baseline (Module 00)

- Process FD limit (`ulimit -n`): 1024 soft / 1048576 hard  ← binds first
- System FD limit: 9223372036854775807 (effectively unbounded)
- Ephemeral port range: 32768-60999 (28,232) — limits the GENERATOR, not the server
- Bytes per platform thread: ~69 KB RSS (died at ~32,000 threads)
- Bytes per virtual thread: ~0.85 KB RSS (1,000,000 fit in ~830 MB)
- Idle container RSS: postgres 38 MB / redis 10 MB
- Bytes per idle TCP socket: ~16 KB userspace + 8-64 KB kernel
```

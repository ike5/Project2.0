# Challenge 00 — Know Your Machine

Solutions in [`solutions/`](./solutions/). Try first.

You can't reason about scale on hardware you haven't measured. These tasks
establish your baseline — every later benchmark in the course is relative to it.
They also front-load the numbers that make Module 01's runtime argument land: if
you don't know what an OS thread costs *before* you meet the event loop, the
event loop's win is just a claim.

## Tasks

1. **Find your hard connection ceiling.**
   Determine, without running a server, the maximum number of TCP connections
   your machine could theoretically accept. Report the three separate limits
   that could bind first:
   - the process file-descriptor limit (`ulimit -n`),
   - the system-wide file-descriptor limit,
   - the ephemeral port range (and explain why this limits the *client* side —
     your load generator — not the server side).

   Write the three numbers and which one binds first in `results.md`.

2. **Measure per-Task vs per-thread cost.**
   Write two small Python programs:
   - one that creates N **asyncio Tasks**, each of which `await asyncio.sleep(30)`,
   - one that creates N **OS threads** (`threading.Thread`), each of which
     `time.sleep(30)`.

   Report the process RSS and **bytes per unit** at N = 10,000 and, for tasks,
   N = 1,000,000. Push the thread version until it fails and **record the error
   and the count** — that failure is the answer, and it's the reason Phase 1
   exists. (Hint: Python threads fail differently than JVM threads; note *how*.)

3. **Establish your Docker overhead.**
   Bring up `infra/compose.dev.yml` and record the steady-state RSS of each
   container after 5 minutes idle (`docker stats --no-stream`). This is the tax
   you pay before writing a line of chat code.

4. **Predict, then measure, fan-out amplification.**
   For a system with 10,000 connected users spread across rooms averaging 50
   members, where each user sends 1 message per 5 minutes:
   - Calculate inbound messages/second.
   - Calculate outbound messages/second.
   - Calculate the amplification factor.

   Then redo it for rooms averaging 500 members. Note how the *inbound* number is
   identical and the outbound number is not. This is Problem 2, in arithmetic.

5. **Stretch — find the true cost of an idle socket.**
   Write a tiny asyncio TCP server that accepts connections and does nothing
   else, and a client that opens 10,000 connections to it and holds them. Measure
   the RSS of **both** processes and compute kernel + userspace bytes per idle
   connection on each side. You now know what an *empty* connection costs —
   before Django, Channels, an asyncio Task, or your session map get involved.
   Module 01 adds each of those on top of this floor.

## Success criteria

- [ ] `results.md` records all three connection limits, with the binding one
      identified and the client-vs-server distinction explained
- [ ] Bytes-per-unit is recorded for asyncio Tasks and OS threads, and the
      thread failure count + error is captured
- [ ] Idle container RSS is recorded for postgres and redis
- [ ] Both amplification calculations are done, with the inbound/outbound
      asymmetry explained in one sentence
- [ ] Stretch: bytes per idle socket is measured on both ends, not guessed

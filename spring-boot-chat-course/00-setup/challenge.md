# Challenge 00 — Know Your Machine

Solutions in [`solutions/`](./solutions/). Try first.

You can't reason about scale on hardware you haven't measured. These tasks
establish your baseline — every later benchmark is relative to it.

## Tasks

1. **Find your hard connection ceiling.**
   Determine, without running a server, the maximum number of TCP connections
   your machine could theoretically accept. Report the three separate limits
   that could bind first:
   - the process file-descriptor limit,
   - the system-wide file-descriptor limit,
   - the ephemeral port range (and explain why this limits the *client* side,
     not the server side).

   Write the three numbers and which one binds first in `results.md`.

2. **Measure your JVM's baseline thread cost.**
   Write a program that starts N platform threads that each sleep for 30
   seconds, and report the RSS of the JVM at N = 1,000 and N = 10,000. Then do
   the same with virtual threads at N = 10,000 and N = 1,000,000.

   Report **bytes per thread** for each. If 1,000,000 platform threads fails,
   that failure *is* the answer — record the error.

3. **Establish your Docker overhead.**
   Bring up `infra/compose.dev.yml` and record the steady-state memory of each
   container after 5 minutes idle. This is the tax you pay before writing a line
   of chat code.

4. **Predict, then measure, fan-out amplification.**
   For a system with 10,000 connected users spread across rooms averaging 50
   members, where each user sends 1 message per 5 minutes:
   - Calculate inbound messages/second.
   - Calculate outbound messages/second.
   - Calculate the amplification factor.

   Then redo it for rooms averaging 500 members. Note how the *inbound* number
   is identical and the outbound number is not.

5. **Stretch — find the cost of a socket.**
   Write a tiny TCP server (any language) that accepts connections and does
   nothing else. Open 10,000 connections to it from a second process. Measure
   the RSS of both processes and compute kernel + userspace bytes per idle
   connection. You now know what an *empty* connection costs, before Spring,
   Jackson, or your session map get involved.

## Success criteria

- [ ] `results.md` exists and records all three connection limits, with the
      binding one identified
- [ ] Bytes-per-thread is recorded for platform and virtual threads
- [ ] Idle container memory is recorded for postgres and redis
- [ ] Both amplification calculations are done, with the inbound/outbound
      asymmetry explained in one sentence
- [ ] Stretch: bytes per idle socket is measured, not guessed

# Challenge 21 — Attack Your Own System

Solutions in [`solutions/`](./solutions/). Try first.

**Authorized testing only — you attack your own local server.**

## Tasks

1. **Threat-model Pulse and find the hole the lab missed.**
   Produce a STRIDE threat model of the full system. The lab closed a specific
   list; find at least one exploitable issue not on it. Prove it, then fix it.

   (Hint: consider the ticket endpoint, the resume path, presence, `receive_json`
   dispatch, and what one valid user can do to another valid user. The
   `database_sync_to_async` threadpool is a bounded resource — can a valid user
   exhaust it?)

2. **Break the rate limiter, then fix it.**
   Find three ways to send more messages than the limits should allow. For each:
   the technique, the messages you got through, and the fix.

   At least one should exploit the interaction between the client-side outbox
   (Module 17) and the server-side token bucket — a client that replays its
   offline queue on reconnect looks exactly like a burst.

3. **Make revocation actually immediate under partition.**
   The lab's revocation uses `group_send` over the Redis channel layer, which is
   Pub/Sub-based and **at-most-once** (Module 07). Show that a node reconnecting to
   Redis at the instant of the push misses the revocation and keeps a revoked user
   connected.

   Fix it with a **durable reconciliation loop** (each node periodically re-reads
   the denylist and evicts any local socket whose `jti` is on it) so revocation is
   *guaranteed* even when the push is lost — and state what the reconciliation
   interval costs you (the worst-case window a revoked user stays connected).

4. **Measure the security overhead honestly.**
   Every defense costs something. Measure the aggregate latency and throughput cost
   of the full security stack versus the insecure Module 04 baseline, on the
   Module 06 harness.

   Then find the single most expensive defense and decide whether it is worth it.

5. **Design moderation for an E2EE room.**
   E2EE breaks server-side moderation. Design a system that provides *some* abuse
   protection for encrypted rooms without breaking the encryption.

   Be honest about what each option can and cannot catch, and its privacy
   tradeoff: client-side scanning, metadata analysis, reputation, reporting.

6. **Stretch — run a red-team exercise.**
   Give someone the deployed system and a goal (read a room they're not in, send as
   another user, take the service down, exfiltrate data). Record time-to-first-
   compromise and what they used.

   Fix everything they find, then run it again.

## Success criteria

- [ ] A STRIDE model with at least one exploitable finding **not** in the lab's
      list, proven and fixed
- [ ] Three rate-limit bypasses demonstrated and fixed, including one exploiting
      the client outbox
- [ ] The Pub/Sub revocation gap proven and closed with a reconciliation loop, the
      cost (worst-case window) stated
- [ ] Aggregate security overhead measured; the most expensive defense identified
      and a keep/drop decision made
- [ ] An E2EE moderation design with an honest capability and privacy analysis
- [ ] Stretch: a red-team exercise with time-to-compromise, fixes, and a re-run

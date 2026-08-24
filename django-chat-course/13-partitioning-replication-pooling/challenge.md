# Challenge 13 — Survive the Failures This Module Introduced

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Restore the guarantees partitioning weakened, and prove it.**
   Attaching the partition key to every unique index changed two guarantees:
   idempotency on `(room_id, client_id)` is now per-partition, and `(room_id,
   seq)` uniqueness is too.

   Write a test that **actually produces** each failure (a retry across a month
   boundary that double-inserts; a `seq` collision across partitions after a Redis
   restart). Then close both holes, at whatever layer you decide is right, and
   state the cost of your fix in latency, storage or operational burden.

2. **Make the replica earn its keep, and know when it isn't.**
   The lab's router sends reads to the replica unless the actor wrote recently.
   That is not enough in either direction:
   - a replica that is 40 seconds behind should not be serving *any* reads;
   - a replica that is 4 ms behind is serving reads that could safely skip the
     sticky window.

   Implement lag-aware routing: measure replica lag continuously, take the replica
   out of rotation above a threshold you justify with numbers, and shrink the
   sticky window when lag is low. Show the failure the naive router produces
   (kill replication and watch reads go stale) and prove yours does not.

3. **Size the pool, don't guess it.**
   `default_pool_size = 25` came from a rule of thumb. Derive it instead: run the
   throughput/latency curve for your actual workload, find the knee, and set the
   pool from the measurement.

   Then break it deliberately — set the pool too small and produce sustained
   `cl_waiting`, and set it too large and reproduce the throughput collapse. Give
   the two symptoms and the dashboard query that distinguishes them, because they
   feel identical to a user.

4. **Turn the outbox relay from a 1-second poll into something better — or prove
   the poll wins.**
   The relay polls once a second, so worst-case publish latency after a crash is
   ~1 s plus the `LOOKBACK_MS` window. Implement a `LISTEN`/`NOTIFY`-driven relay,
   remembering what Part F taught you about `LISTEN` and PgBouncer.

   Measure both on: publish latency after a crash, idle cost (queries/s when there
   is nothing to do), behaviour when the relay has been down for an hour, and
   behaviour when 50,000 rows arrive at once. Recommend one, with the condition
   that would reverse the recommendation.

5. **Stretch — write the failover runbook and then execute it.**
   Promote the replica to primary while the application is under load. Measure
   RPO (messages accepted by the old primary that did not survive) and RTO (time
   until sends succeed again).

   Then find the specific thing in *this module's* design that makes the RPO
   non-zero and fix it. Compare your numbers against `synchronous_commit = on`
   versus `remote_apply` for the outbox write, and say which you would ship.

## Success criteria

- [ ] Both partitioning-weakened guarantees are reproduced by a failing test, then
      closed, with the cost of each fix stated
- [ ] Lag-aware routing implemented; the naive router's stale-read failure is
      demonstrated and the new one's absence is proven under the same conditions
- [ ] `default_pool_size` derived from a measured curve, with both the too-small
      and too-large failure modes reproduced and a query that tells them apart
- [ ] `LISTEN`/`NOTIFY` relay built and measured against the poll on all four axes,
      with a recommendation and a reversing condition
- [ ] Stretch: a failover executed under load with RPO and RTO numbers, the
      non-zero RPO explained and fixed, and a `synchronous_commit` recommendation

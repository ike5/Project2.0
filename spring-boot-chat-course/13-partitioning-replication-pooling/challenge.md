# Challenge 13 — Operate It

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Automate partition management, and prove the failure mode first.**
   Let the clock roll past your last provisioned partition with the DEFAULT
   partition dropped. Show exactly what happens to inserts.

   Then automate creation (pg_partman or a scheduled job) and retention. Your
   solution must include an alert that fires *before* partitions run out, not
   after.

2. **Make the outbox relay horizontally safe and measure it.**
   Run 3 relay instances against one outbox. Prove with a test that no message is
   published twice by two relays, and measure throughput at 1, 2 and 4 relays.

   Then find the point where `FOR UPDATE SKIP LOCKED` stops scaling and explain
   why.

3. **Handle a poisoned outbox row.**
   A row whose payload can't be published (malformed, or a room that no longer
   exists) blocks nothing — `SKIP LOCKED` moves past it — but its `attempts`
   climbs forever and it's retried every 50 ms.

   Implement a dead-letter policy with exponential backoff. Prove a poison row
   doesn't consume measurable relay capacity.

4. **Measure replica lag under realistic load and set an SLO.**
   Determine what drives lag on your setup: write volume, replica read load, or
   long-running queries. Vary each independently.

   Then set a lag SLO, implement an alert, and implement automatic replica
   removal from the read pool when it exceeds the threshold.

5. **Break PgBouncer's transaction mode on purpose.**
   Find and demonstrate three things that break under `pool_mode = transaction`
   but work under `session`. For each, show the error and the fix.

   Then decide which of them Pulse actually needs, and how you'd accommodate it.

6. **Stretch — implement the LSN-wait read consistency.**
   Replace the sticky window with the precise version: return the write's LSN to
   the client, have the client send it with subsequent reads, and have the read
   wait for the replica to catch up (with a timeout that falls back to the
   primary).

   Measure the replica read share and p99 versus the sticky window. Then say
   which you'd ship and why.

## Success criteria

- [ ] The out-of-partitions failure is demonstrated, then automated away, with a
      *predictive* alert
- [ ] 3 relays proven not to double-publish; throughput measured at 1/2/4 with a
      scaling limit explained
- [ ] Poison outbox rows are dead-lettered with backoff, with capacity impact
      measured
- [ ] Replica lag drivers isolated; an SLO, alert, and automatic pool removal
      exist
- [ ] Three transaction-mode breakages demonstrated with errors and fixes, and a
      decision for Pulse
- [ ] Stretch: LSN-wait implemented and compared against the sticky window with a
      shipping recommendation

# Challenge 07 — Quantify the Backplane

Solutions in [`solutions/`](./solutions/). Try first.

The lab established that Redis moved the wall rather than removing it. These
tasks find the new wall precisely, close the two holes the lab left open, and
force you to write down the decision you would defend in a review.

## Tasks

1. **Measure subscription amplification, and extrapolate the wall.**
   Run 1, 2, 4, 8 and 16 worker processes with 1,000 rooms and 20,000
   connections spread randomly. For each, measure:
   - distinct group keys in Redis, and the mean number of *worker processes*
     per group (`layer_probe.py amplification` gives you both);
   - Redis's per-`group_send` cost from `INFO commandstats`, split into the
     part that is fixed and the part that scales with worker count;
   - Redis's `total_net_output_bytes` per inbound message.

   Then answer two questions with numbers. At what worker count does Redis's
   single thread pass 95%? And at what point does its *outbound bandwidth*
   pass 1 Gbit/s? Which limit arrives first, and by how much — this is the
   thing that decides whether Module 18 needs Cluster for throughput or only
   for availability.

2. **Close the group-membership hole properly.**
   The lab's 300-second refresh turns "lost forever" into "lost for up to five
   minutes". That is not good enough for a 69.5% delivery outage.

   Build a detector that notices Redis lost its state and repairs membership in
   seconds, not minutes. `INFO server`'s `run_id` changes on every restart, and
   `INFO stats`'s `sync_full` and the `master_replid` are also candidates —
   pick one, justify it, and say what it does *not* catch (there is at least
   one important case: a `FLUSHALL`, and a Sentinel failover to a replica that
   was behind).

   Measure the time from restart to full delivery, before and after. Then state
   the cost of your detector in Redis operations per second at 8 workers and
   20,000 connections, and say whether you would run it at 16.

3. **Saturate a mailbox and describe the blast radius.**
   `capacity` is per worker mailbox. Find the offered load at which a mailbox
   stays non-empty, then push past it until the `EVAL` starts skipping keys.

   Answer precisely: when a mailbox is at capacity, *what* is dropped, *who*
   notices, and *what is logged*? Compare that blast radius with Module 04's
   in-memory `ChannelFull` and with Module 06's per-connection write queue —
   they fail at three different scopes and one of them is much worse than the
   other two. Then add the gauge and the alert you would actually page on, and
   argue for a `capacity` value using your own numbers rather than the lab's.

4. **Price sticky sessions.**
   With 10,000 connected clients, measure how many are disconnected when you
   (a) add a third app instance and (b) remove one, under three load-balancer
   strategies: `hash $cookie consistent`, `ip_hash`, and no stickiness at all.
   Also measure the distribution evenness of each.

   Then answer with data: what specifically breaks if Pulse removes stickiness
   entirely? Measure the reconnect cost to the same worker versus a different
   one. Make a recommendation and name the condition that would reverse it.

5. **Stretch — put the message path on the Pub/Sub layer and defend the
   result.**
   The lab measured `RedisPubSubChannelLayer` at roughly 2.3× the knee and a
   quarter of Redis's CPU, and rejected it for the message path on
   backpressure grounds. Test that reasoning instead of trusting it: run the
   Module 06 slow-consumer attack against the Pub/Sub layer at 8 workers and
   measure how long a worker survives, and whether `--ws-max-queue` alone is
   enough to save it.

   Then write the paragraph you would put in an architecture decision record
   choosing one layer for the message path — including the measured numbers on
   both sides, the failure mode you are accepting, and the condition under
   which you would switch. Compare your conclusion with the JVM twin's ADR in
   [`07-scale-out-redis-pubsub`](../../spring-boot-chat-course/07-scale-out-redis-pubsub/solutions/solution.md):
   it chose Redis over a real broker for reasons that are only partly the same.

## Success criteria

- [ ] Amplification is measured at five worker counts, with Redis's cost split
      into fixed and per-worker terms, and both the CPU wall and the bandwidth
      wall extrapolated with the earlier one named
- [ ] A restart detector repairs group membership in seconds, with a measured
      before/after time-to-recovery, a stated Redis cost, and at least one case
      it does not catch
- [ ] Mailbox saturation is reproduced, with what-is-dropped / who-notices /
      what-is-logged answered, the blast radius compared against two other
      failure scopes, and a `capacity` argued from your own numbers
- [ ] Sticky-session cost is measured for add and remove across three
      strategies, with reconnect cost measured and a recommendation plus its
      reversing condition
- [ ] Stretch: the Pub/Sub layer's backpressure failure is measured rather than
      assumed, and an ADR paragraph names the numbers, the accepted failure
      mode, and the switching condition

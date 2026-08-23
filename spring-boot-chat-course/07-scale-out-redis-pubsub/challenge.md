# Challenge 07 — Quantify the Backplane

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Measure subscription amplification.**
   Run 1, 2, 4 and 8 instances with 1,000 rooms and users distributed randomly.
   For each, measure:
   - how many Redis channels each instance is subscribed to,
   - Redis's outbound bandwidth (`INFO stats` → `total_net_output_bytes`) per
     inbound message,
   - the amplification factor.

   Plot instances vs Redis outbound. Extrapolate: at what instance count does
   Redis's outbound exceed 1 Gbit/s for your workload? That's your next wall.

2. **Fix the split-view hazard.**
   The lab publishes to the local broker *then* to Redis. If the Redis publish
   fails, local users have the message and remote users never will — permanently
   inconsistent, with no error surfaced.

   Reproduce it deterministically. Then implement a fix that guarantees either
   everyone gets it or nobody does, *without* introducing a distributed
   transaction. Explain what you traded away.

3. **Break the listener thread pool.**
   `RedisMessageListenerContainer`'s executor is a queue you added to the system.
   Find its saturation point: how many inbound fan-out messages/second before its
   queue depth stays non-zero?

   Then answer: what happens when its `queueCapacity` fills? Is the failure mode
   better or worse than the outbound channel's? Instrument it with a gauge.

4. **Make the poison-message handler correct.**
   The lab catches `Exception` and logs. Prove this is necessary by publishing a
   malformed message and showing the listener survives. Then prove it's
   *insufficient*: what happens if the failure is an `OutOfMemoryError`, or if
   every message is poison?

   Implement a bounded failure policy — e.g. circuit-break the room after N
   consecutive failures, and surface it as an unhealthy readiness probe.

5. **Sticky sessions: measure what they cost.**
   With `hash $cookie_pulse_node consistent`, measure how many clients are
   disconnected when you (a) add a third instance and (b) remove one. Compare
   against `ip_hash` and against no stickiness at all.

   Then answer with data: is stickiness worth it for Pulse? What specifically
   breaks if you remove it?

6. **Stretch — compare against the STOMP relay.**
   Run RabbitMQ with the STOMP plugin alongside your Redis backplane. Run the
   identical k6 workload against both. Report p50/p95/p99, CPU and memory of the
   broker tier, and messages lost during an equivalent `docker pause` drill.

   Then write the paragraph you'd put in an architecture decision record
   recommending one — including the condition under which you'd switch.

## Success criteria

- [ ] Subscription amplification is measured at 4 instance counts with an
      extrapolated Redis bandwidth wall
- [ ] The split-view hazard is reproduced and fixed, with the tradeoff named
- [ ] The listener pool's saturation point is measured and gauged, with its
      failure mode compared to the outbound channel's
- [ ] Poison-message handling survives malformed input and has a bounded failure
      policy wired to readiness
- [ ] Sticky-session cost is measured for add and remove, across three LB
      strategies, with a data-backed recommendation
- [ ] Stretch: Redis vs RabbitMQ measured head to head, with an ADR paragraph

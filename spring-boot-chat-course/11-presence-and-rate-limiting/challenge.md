# Challenge 11 — Bound the Unbounded

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Collapse four round trips into one.**
   The lab's rate limiter makes four sequential Redis calls per message, using
   most of Module 08's five-round-trip budget. Rewrite it as a single Lua script
   checking all four buckets atomically.

   You will hit the Cluster same-slot constraint — the four keys must hash
   together, but they're keyed by different things (user, ip, room). Solve it,
   and explain what you gave up.

2. **Make presence work across a node failure.**
   Kill a node holding 3,000 connections. Measure how long until those users show
   as offline to everyone else, and how long until they show as online again
   after reconnecting.

   Then reduce both numbers without reducing the TTL (which would increase
   heartbeat traffic). Report before and after.

3. **Find the sweeper's scaling limit.**
   The sweeper does one `MGET` over all watched users every 20 seconds. Measure
   its cost at 10k, 100k and 1M watched users.

   Find where it breaks and fix it. (Hint: `MGET` with 1,000,000 keys is a single
   command on a single thread — revisit Module 08.)

4. **Add a "last seen" feature without destroying your system.**
   Product wants "last seen 3 minutes ago." This is the feature that most
   directly conflicts with everything in this module.

   Design and implement it. State the precision you offer, the update rate it
   costs, and the privacy control you added. Measure the traffic increase versus
   coarse presence.

5. **Make rate limiting fair under a distributed attack.**
   200 accounts from 200 IPs each send just under every limit. Individually
   legitimate; collectively a flood.

   Detect it and respond, without harming legitimate users during a genuine
   traffic spike. Explain how you distinguish the two.

6. **Stretch — implement fencing tokens.**
   Take the presence sweeper's lock and make it actually safe: the lock returns a
   monotonically increasing token, and the protected operation rejects stale
   tokens.

   Then demonstrate the safety property by pausing the lock holder past the TTL
   and showing the stale write is rejected. Finally, explain why almost nobody
   does this.

## Success criteria

- [ ] Rate limiting is one round trip, works in Cluster, with the tradeoff named
- [ ] Node-failure presence transition times measured and improved without
      lowering the TTL
- [ ] Sweeper cost measured at three scales, with the breaking point found and
      fixed
- [ ] "Last seen" is implemented with a stated precision, cost, and privacy
      control, and the traffic delta is measured
- [ ] A distributed low-and-slow attack is detected and mitigated, with the
      false-positive reasoning explained
- [ ] Stretch: fencing tokens demonstrably reject a stale writer after a pause

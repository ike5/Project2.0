# Challenge 04 — Make the Broker Show You Its Limits

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Enforce that clients cannot publish to `/topic`.**
   Right now a malicious client can `SEND` directly to `/topic/room.7`,
   bypassing your controller entirely — no validation, no persistence, no
   authorization, and they can impersonate anyone.

   Prove the hole exists first (send a forged message as "admin" from
   `websocat`). Then close it with a `ChannelInterceptor` that rejects any
   client frame whose destination doesn't start with `/app` or `/user`. Prove it's
   closed.

2. **Enforce room membership on SUBSCRIBE.**
   Any connected user can currently subscribe to `/topic/room.99` whether or not
   they're a member. Add authorization at subscribe time, backed by the
   `room_members` table from Module 02.

   Then answer: why is checking at SUBSCRIBE time necessary but *not sufficient*?
   (Hint: what happens when a user is removed from a room while subscribed?)
   Implement the missing half.

3. **Make a slow consumer hurt, then prove your limits save you.**
   Write a client that connects, subscribes to a busy room, and then **stops
   reading its socket** (open the TCP connection but never `recv`). Blast 10,000
   messages into the room.

   - With `setSendBufferSizeLimit` removed, measure heap growth.
   - With it set to 512 KB, show the session is closed and the heap is flat.

   Record which exception appears in the log and at roughly what message count.

4. **Find the channel queue ceiling.**
   Using the `stomp.channel.queued` metric, determine how many messages/second
   into a single 200-member room it takes to make `clientOutboundChannel`'s queue
   depth stay persistently above zero. That's your saturation point.

   Then set `queueCapacity` to 100 and repeat. What happens when the queue is
   full? Find the exception, and explain why a bounded queue that throws is
   better than an unbounded one that doesn't.

5. **Measure the fan-out cost curve.**
   Measure p99 end-to-end latency (send → last recipient receives) for rooms of
   10, 100, 1,000, and 5,000 members, at a fixed 10 messages/second inbound.
   Plot it.

   The curve should not be linear. Explain what changes shape and why. State the
   room size at which your single node stops meeting a 200 ms p99 budget.

6. **Stretch — replace the simple broker with a real one.**
   Run RabbitMQ with the STOMP plugin and switch to
   `registry.enableStompBrokerRelay("/topic", "/queue")`. Redo Part I of the lab
   (two instances, two users).

   It should now work. Write 200 words on what you gained, what you gave up, and
   why the rest of this course builds a Redis backbone instead of just using
   this. Be specific about operational cost, delivery semantics, and what happens
   when the broker itself needs to be highly available.

## Success criteria

- [ ] The `/topic` forgery hole is demonstrated, then closed and re-tested
- [ ] Subscribe-time authorization works, and the revocation gap is identified
      and handled
- [ ] A slow consumer is shown to grow the heap without limits, and to be
      cleanly disconnected with them
- [ ] The outbound channel saturation point is measured in messages/second
- [ ] The bounded-queue rejection behaviour is observed and its exception named
- [ ] A fan-out latency curve exists for 4 room sizes, with the non-linearity
      explained and a p99 budget crossover identified
- [ ] Stretch: STOMP relay works across two instances, with a written comparison

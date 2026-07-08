# Challenge 11 — Concurrency

Solution in [`solutions/`](./solutions/). Try first.

## Tasks

1. **`AtomicLong` counter under contention.** Build a `Counter` backed
   by `AtomicLong`. Run 8 threads, each calling `increment` 10,000
   times. Confirm the final value is exactly 80,000.

2. **`CompletableFuture` thenCompose chain.** Build
   `CompletableFuture<String> fetchUserName(long id)` that returns
   `"Ada Lovelace"` for id=1 and `"Grace Hopper"` for id=2 (synthetic
   data — you decide the impl). Compose: `fetchUser` → `thenCompose(
   u -> fetchAddress(u))` → `thenApply(a -> a.city())`. Show the
   final string.

3. **`thenCombine` of two async sources.** Build two
   `CompletableFuture<Integer>`s that return values after a small
   delay; combine them into the sum using `thenCombine`. Compare to
   doing it sequentially with two `.get()` calls.

4. **A `BlockingQueue` producer / consumer.** Build
   `class ProducerConsumer` with a `BlockingQueue<Integer> queue` and
   `start()` that spawns one producer thread (puts `0..99` into the
   queue with a tiny sleep) and one consumer thread (polls and prints).
   `stop()` joins both. Show that the consumer sees the producer's
   items in order.

5. **`ConcurrentHashMap` with `computeIfAbsent`.** Build
   `ConcurrentMap<String, List<String>> byTag` and a method
   `add(String tag, String value)` that uses `computeIfAbsent` to
   ensure each tag has a list. Run the same `add` from 4 threads; the
   list for each tag should be a single instance (no duplication).

## Success criteria

- [ ] `Counter` ends at exactly 80,000 after 8 × 10,000 increments.
- [ ] The `thenCompose` chain returns the city name for the right user.
- [ ] `thenCombine` returns the sum; the two fetches ran in parallel.
- [ ] The producer / consumer pipeline prints 0..99 in order.
- [ ] `add` from 4 threads produces one bucket per tag (no duplicates).

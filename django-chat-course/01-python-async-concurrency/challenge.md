# Challenge 01 — Build a Session Registry That Doesn't Lie (and Can't Span Processes)

Solutions in [`solutions/`](./solutions/). Try first.

In Module 04 you'll need a component that tracks every connected session on a
worker — which user, which rooms — mutated as clients connect and disconnect, and
read on every single fan-out. Getting it wrong costs you correctness *and*
memory. Build it now, in pure asyncio, before Channels is in the way — and prove
to yourself the thing that defines the whole course: **it lives in one worker
process and cannot see any other.**

> This is the Python twin of the JVM course's
> [Challenge 01](../../spring-boot-chat-course/01-java21-concurrency/challenge.md).
> There, the hard part was thread-safety across thousands of virtual threads
> (`ConcurrentHashMap`, no `synchronized`). Here, the hard part is the *opposite*:
> a single event loop means you need **no locks at all** — and the real wall is
> the process boundary. Notice how the runtime changes the problem.

## Tasks

1. **Implement an async `SessionRegistry`.**
   ```python
   class SessionRegistry:
       def connect(self, session_id: str, user_id: str) -> None: ...
       def disconnect(self, session_id: str) -> None: ...
       def subscribe(self, session_id: str, room_id: str) -> None: ...
       def sessions_in_room(self, room_id: str) -> set[str]: ...
       def rooms_for(self, session_id: str) -> set[str]: ...
       def active_connections(self) -> int: ...
   ```
   Requirements:
   - It's driven from **one event loop**, so it needs **no locks** — but you must
     say *in a comment why* that's safe, and exactly which operation would break
     it (hint: an `await` in the middle of a mutation).
   - `disconnect` must remove the session from **every** room it joined — no
     leaks. A registry that grows forever is the #1 chat memory bug.
   - When a room's last member leaves, its key must be **removed**, not left as an
     empty set. (An app where every DM is a room leaks one empty set per
     conversation, forever.)
   - `active_connections()` must be exact.

2. **Write a concurrency test that catches a broken implementation.**
   Spawn 10,000 asyncio Tasks that each connect, subscribe to 1–5 of 100 rooms,
   `await asyncio.sleep(0)` (to interleave), then disconnect. After they all
   finish, assert:
   - `active_connections() == 0`
   - every room's subscriber set is empty
   - no room key leaked with an empty set left behind (`len(registry._members) == 0`)

   Write a *broken* version first (forget the empty-set cleanup) and confirm your
   test catches it. A test that passes against broken code is not a test.

3. **Add bounded, cancellable fan-out.**
   Add `async def broadcast(self, room_id, payload, send)` that delivers to every
   session in the room *concurrently*, but with **at most 100 deliveries in
   flight at once**, and which cancels all remaining deliveries if any one
   raises. Use an `asyncio.Semaphore` for the bound and an `asyncio.TaskGroup`
   for the cancellation — and justify why you need *both* (what does each one
   guarantee that the other doesn't?).

4. **Prove it can't span processes.**
   Run the registry in **two separate processes** (two `python` invocations, or
   `multiprocessing.Process`). Connect session `A` in process 0 and session `B`
   in process 1, both subscribed to `room-1`. From process 0, call
   `sessions_in_room("room-1")`. Show that it returns `{A}`, not `{A, B}` —
   process 0's registry has no idea process 1's session exists. Write one
   paragraph explaining why this means the `InMemoryChannelLayer` cannot deliver
   a message across workers on one machine, and why that forces Redis in Module
   04/07 *sooner* than the JVM course needs it.

5. **Stretch — measure the `sync_to_async` threadpool as a bounded resource.**
   `sync_to_async`'s default executor is a bounded thread pool. Fire 2,000
   coroutines that each call a `sync_to_async`-wrapped function which
   `time.sleep(0.05)` (simulating a blocking ORM call). Measure p50/p99 latency.
   Then bound admission with an `asyncio.Semaphore(N)` and find the N that
   restores a flat p99. Explain, in two sentences, why the *unbounded* version's
   p99 is bad even though the event loop itself never blocked — and connect it to
   the Part F trap from the lab.

## Success criteria

- [ ] `SessionRegistry` is correct with **zero locks**, and the comment explains
      why the single loop makes that safe (and what would break it)
- [ ] `disconnect` provably leaks nothing — rooms *and* empty room keys are gone
- [ ] `active_connections()` is exact under 10,000-task churn
- [ ] The concurrency test fails against a deliberately broken (leaky) version
- [ ] `broadcast` bounds in-flight deliveries **and** cancels siblings on failure,
      with the role of the Semaphore vs the TaskGroup explained
- [ ] The two-process demo shows the registry cannot span processes, with the
      Module-04/07 consequence written out
- [ ] Stretch: the `sync_to_async` threadpool bound is measured and the
      admission fix found

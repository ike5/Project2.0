# Challenge 05 — Observer pattern

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Implement `HitCounter`** in `05-observer-pattern/code/hit_counter_mine.py` from scratch. Submit to LeetCode 362.
2. **Build an `EventBus`** in `05-observer-pattern/code/event_bus.py` with `on(event, fn)`, `off(event, fn)`, and `emit(event, *args)`. Subscribe three different functions to a `"tick"` event; one prints, one logs to a list, one increments a counter. Emit 3 ticks. Unsubscribe the counter. Emit 2 more ticks. Print the log and counter.
3. **Write `pytest` tests** for both in `05-observer-pattern/code/test_mine.py`.

## Success criteria

- [ ] LeetCode 362 accepts your `HitCounter`.
- [ ] `EventBus` correctly delivers events to subscribers, supports unsubscribe, and the log/counter values match what you emitted.
- [ ] All tests pass.

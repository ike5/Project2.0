# Lab 03 — Classes & `self`

**You'll:** build a `ParkingSystem` class, poke at `self` in the REPL, and write a couple of your own tiny classes. ⏱️ ~30 min.

---

## Part A — Run the ParkingSystem demo

```bash
python 03-classes-and-self/code/parking_system.py
```

✅ You should see a sequence of `True` / `False` that matches the LeetCode prompt's example.

## Part B — REPL exploration

```bash
python -i 03-classes-and-self/code/parking_system.py
```

In the REPL:

```python
>>> ps = ParkingSystem(1, 1, 0)
>>> type(ps)
<class '__main__.ParkingSystem'>
>>> ps.__dict__
{'slots': [0, 1, 1, 0]}
>>> ps2 = ParkingSystem(0, 0, 2)
>>> ps.slots
[0, 1, 1, 0]
>>> ps2.slots
[0, 0, 0, 2]              # independent — each instance gets its own
```

This is the difference between *instance state* and *class state*. Both `ps` and `ps2` are `ParkingSystem` objects, but they have separate `slots` lists.

Exit the REPL with `exit()`.

## Part C — pytest

```bash
python -m pytest 03-classes-and-self/code/test_parking_system.py
```

✅ All tests pass.

## Part D — Write your own class

Open `03-classes-and-self/code/counter.py`. Implement a `Hits` class with:

- `__init__(self)` — starts a counter at `0`.
- `record(self)` — increments by `1`.
- `record_n(self, k)` — increments by `k`.
- `total(self)` — returns the current count.
- `reset(self)` — sets the count to `0`.

Run it with `python 03-classes-and-self/code/counter.py` and the demo at the bottom should pass.

---

When everything passes, move to the challenge.

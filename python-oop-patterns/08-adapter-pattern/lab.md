# Lab 08 — Adapter pattern

**You'll:** build a `PrintAdapter`, then build the LeetCode 155 Min Stack. ⏱️ ~30 min.

---

## Part A — PrintAdapter

```bash
python 08-adapter-pattern/code/print_adapter.py
```

✅ You should see `Hello, world!` with the configured prefix.

## Part B — Min Stack

```bash
python 08-adapter-pattern/code/min_stack.py
```

✅ You should see the LeetCode 155 example: `top -> 0`, `getMin -> -2`, after pop `top -> 2`, `getMin -> 0`.

Read the implementation. Note the parallel `mins` list.

## Part C — Add the tuple variant

Open `08-adapter-pattern/code/min_stack_tuple.py`. There's a one-list version. Run it and confirm it produces the same output.

## Part D — pytest

```bash
python -m pytest 08-adapter-pattern/code/test_min_stack.py
```

✅ All tests pass.

---

When everything passes, move to the challenge.

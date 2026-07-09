# Lab 07 — Factory pattern

**You'll:** build a `Notifier.for(channel)` factory, then build the LeetCode 707 linked list with a `from_array` factory classmethod. ⏱️ ~40 min.

---

## Part A — Notifier factory

```bash
python 07-factory-pattern/code/notifier_factory.py
```

✅ You should see three different output formats — email, SMS, push — all constructed by `Notifier.for_channel(...)`.

## Part B — Date factory

```bash
python 07-factory-pattern/code/date_factory.py
```

✅ You should see dates created two different ways.

## Part C — Linked list

```bash
python 07-factory-pattern/code/linked_list.py
```

✅ You should see a list `[1, 2, 3]` built from an array, then `get(1) == 2`, `deleteAtIndex(1)` removes the `2`, etc.

Read the implementation. Note the sentinel `head` node — it makes `addAtIndex(0, val)` a one-step operation. Without a sentinel, you'd have to special-case the head.

## Part D — pytest

```bash
python -m pytest 07-factory-pattern/code/test_linked_list.py
```

✅ All tests pass.

---

When everything passes, move to the challenge.

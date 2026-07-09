# Module 08 — The adapter pattern

**Python skill:** wrapping one interface behind another. A list as a stack.
**LeetCode problem:** [155. Min Stack](https://leetcode.com/problems/min-stack/) · Easy/Medium.
**Time:** ~1.5 h.

---

## 1. The pattern

An **adapter** wraps an object and translates its interface to a *different* one. The wrapper has the interface the caller wants; the inner object has the interface that exists.

```python
class PrintAdapter:
    """Adapt the built-in `print` to a class with a .log(msg) method."""
    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix

    def log(self, msg: str) -> None:
        print(self.prefix + msg)
```

The caller says `adapter.log("hi")`; the adapter translates that to `print(prefix + "hi")`. The caller never has to know that `print` exists.

## 2. The classic LeetCode example: Min Stack

> [155. Min Stack](https://leetcode.com/problems/min-stack/)
>
> Design a stack that supports `push`, `pop`, `top`, and `getMin` in O(1) time (or amortized O(1)).
>
> - `MinStack()` — empty stack.
> - `push(val)` — push `val` onto the stack.
> - `pop()` — pop the top.
> - `top()` — return the top element.
> - `getMin()` — return the smallest element in the stack.

A normal Python list is a stack — `append` is push, `pop()` is pop, `xs[-1]` is top. The problem is `getMin`: a single list can't answer that in O(1) on its own.

The standard trick: keep a *parallel* list of running minimums. When you push `val`, push `min(val, last_min)` onto the mins list. When you pop, pop from both:

```python
class MinStack:
    def __init__(self) -> None:
        self.stack: list[int] = []
        self.mins:  list[int] = []       # mins[i] = min(stack[:i+1])

    def push(self, val: int) -> None:
        self.stack.append(val)
        if not self.mins:
            self.mins.append(val)
        else:
            self.mins.append(min(val, self.mins[-1]))

    def pop(self) -> None:
        self.stack.pop()
        self.mins.pop()

    def top(self) -> int:
        return self.stack[-1]

    def getMin(self) -> int:
        return self.mins[-1]
```

This is the *adapter* framing: `MinStack` adapts a plain `list` to support a richer API (`getMin`). The list is the inner object; `MinStack` is the wrapper.

## 3. The alternative: store (val, min) pairs

You can also keep one list of `(val, current_min)` tuples:

```python
class MinStack:
    def __init__(self) -> None:
        self.stack: list[tuple[int, int]] = []    # (val, min-so-far)

    def push(self, val: int) -> None:
        cur_min = val if not self.stack else min(val, self.stack[-1][1])
        self.stack.append((val, cur_min))

    def pop(self) -> None:
        self.stack.pop()

    def top(self) -> int:
        return self.stack[-1][0]

    def getMin(self) -> int:
        return self.stack[-1][1]
```

Same time complexity, slightly less memory. Either is fine.

## 4. Anti-patterns

- **Looping over the stack to find the min.** That makes `getMin` O(n), which LeetCode 155 forbids.
- **Storing the stack in a `deque` without reason.** `list` is fine for stack operations (`append` and `pop()` are O(1) at the end). `deque` is for queues.
- **Trying to compute the min from scratch on every `getMin`.** The whole point is O(1).

---

**→ Next: [Module 09 — Iteration & comprehensions](./../09-iteration-and-comprehensions/)**

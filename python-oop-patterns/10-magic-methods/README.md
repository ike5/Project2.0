# Module 10 — Magic methods & iteration

**Python skill:** `__repr__`, `__len__`, `__getitem__`, `__iter__`, `__contains__` — making your class behave like a built-in.
**LeetCode problem:** [622. Design Circular Queue](https://leetcode.com/problems/design-circular-queue/) · Medium.
**Time:** ~2 h.

---

## 1. What "magic methods" are

Magic methods (or *dunder* methods, for "double underscore") are the hooks Python calls when you use built-in syntax:

| You write        | Python calls        |
|------------------|---------------------|
| `len(x)`         | `x.__len__()`       |
| `x[i]`           | `x.__getitem__(i)`  |
| `x[i] = v`       | `x.__setitem__(i, v)` |
| `for y in x`     | `x.__iter__()`      |
| `y in x`         | `x.__contains__(y)` |
| `x == y`         | `x.__eq__(y)`       |
| `repr(x)`        | `x.__repr__()`      |
| `print(x)`       | `x.__str__()` (falls back to `__repr__`) |
| `hash(x)`        | `x.__hash__()`      |
| `with x:`        | `x.__enter__()` / `x.__exit__()` |

If your class has these, it works seamlessly with the rest of Python. If it doesn't, you have to write `.size()`, `.get(i)`, etc., and *all* the rest of the language has to learn your custom API.

## 2. `__repr__` and `__str__`

`__repr__` is the developer-facing string. Aim for **unambiguous and re-creatable**:

```python
class Stack:
    def __init__(self):
        self._data: list[int] = []

    def push(self, x): self._data.append(x)
    def pop(self):     return self._data.pop()

    def __repr__(self):
        return f"Stack({self._data!r})"
```

`Stack([1, 2, 3])` round-trips through `repr` — copy-paste it into the REPL and you get the same object.

`__str__` is the user-facing string. If you don't define it, `print(x)` uses `__repr__`. For most LeetCode classes, defining `__repr__` is enough.

## 3. The iteration protocol

For an object to be iterable, it needs an `__iter__` method that returns an iterator. The simplest way: return `iter(self._data)`.

```python
class Stack:
    ...
    def __iter__(self):
        return iter(self._data)
```

Now `for x in stack` works, and so does `list(stack)`, `sum(...)`, etc.

## 4. `__len__`, `__getitem__`, `__contains__`

```python
class Stack:
    ...
    def __len__(self):
        return len(self._data)

    def __getitem__(self, i):
        return self._data[i]

    def __contains__(self, x):
        return x in self._data
```

Once these are defined:

- `len(stack)` works.
- `stack[0]`, `stack[-1]`, `stack[1:3]` all work (because `__getitem__` is used for slices too).
- `42 in stack` works.

## 5. The LeetCode problem

> [622. Design Circular Queue](https://leetcode.com/problems/design-circular-queue/)
>
> Design a circular queue with `enQueue`, `deQueue`, `Front`, `Rear`, `isEmpty`, `isFull`, all in O(1).
>
> - `MyCircularQueue(k)` — initialize with capacity `k`.
> - `enQueue(value)` — insert; return `False` if full.
> - `deQueue()` — delete the front; return `False` if empty.
> - `Front()` — return the front element, or `-1` if empty.
> - `Rear()` — return the rear element, or `-1` if empty.
> - `isEmpty()` / `isFull()`.

The standard implementation uses a fixed-size list and two indices (`head`, `tail`):

```python
class MyCircularQueue:
    def __init__(self, k: int) -> None:
        self.data = [0] * k
        self.head = 0
        self.count = 0
        self.cap = k

    def enQueue(self, value: int) -> bool:
        if self.isFull():
            return False
        tail = (self.head + self.count) % self.cap
        self.data[tail] = value
        self.count += 1
        return True

    def deQueue(self) -> bool:
        if self.isEmpty():
            return False
        self.head = (self.head + 1) % self.cap
        self.count -= 1
        return True

    def Front(self) -> int:
        if self.isEmpty():
            return -1
        return self.data[self.head]

    def Rear(self) -> int:
        if self.isEmpty():
            return -1
        tail = (self.head + self.count - 1) % self.cap
        return self.data[tail]

    def isEmpty(self) -> bool:
        return self.count == 0

    def isFull(self) -> bool:
        return self.count == self.cap
```

Notice this is *almost* a list with extra behavior. The "magic" version (the challenge) wraps this with `__len__`, `__iter__`, etc. so the queue looks and feels like a Python container.

## 6. Anti-patterns

- **Overriding `__eq__` and forgetting `__hash__`.** Your object becomes unhashable, so you can't use it as a dict key. Define `__hash__ = lambda self: id(self)` (or a real hash) if you want to keep it hashable.
- **Making `__getitem__` do work beyond indexing.** If you do that, the object won't behave like a real list.
- **Returning `None` from `__repr__`.** It should always return a `str`.

---

**→ Next: [Module 11 — Composition over inheritance](./../11-composition/)**

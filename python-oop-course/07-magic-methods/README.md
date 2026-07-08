# Module 07 — Magic Methods

**Goal:** Make your objects work with `print`, `==`, `+`, `len`, `in`, `for`, and the `with` statement — by implementing the right **dunder methods**. ⏱️ ~2 h · 🎯 Prereq: 06.

---

## 1. What "dunder" means

**Dunder** = "double underscore." Dunder methods are the hooks Python calls when you use the language's built-in syntax on an object. They're also called *magic methods* or *special methods*. They always have names like `__init__`, `__repr__`, `__add__`.

You almost never call dunder methods directly. You write `a + b`, and Python calls `a.__add__(b)` (or `b.__radd__(a)`). You write `len(s)`, and Python calls `s.__len__()`.

The list of useful ones isn't that long. Here are the ones you'll actually use:

| You write | Python calls | Purpose |
|---|---|---|
| `repr(x)` / `x` in REPL | `x.__repr__()` | Developer-facing string form. |
| `str(x)` / `print(x)` | `x.__str__()` | User-facing string form. Defaults to `__repr__`. |
| `f"{x}"` | `x.__format__()` | Used by f-strings and `format()`. |
| `x == y` | `x.__eq__(y)` | Equality. |
| `x < y` | `x.__lt__(y)` | Less than. |
| `hash(x)` | `x.__hash__()` | Hashing (for dict keys and set members). |
| `x + y` | `x.__add__(y)` | Addition. |
| `x[k]` | `x.__getitem__(k)` | Indexing / subscripting. |
| `len(x)` | `x.__len__()` | Length. |
| `for v in x` | `iter(x)` → `x.__iter__()` | Iteration. |
| `with x as y` | `x.__enter__()`, `x.__exit__()` | Context manager. |
| `bool(x)` | `x.__bool__()` | Truthiness. |
| `x()` | `x.__call__()` | Calling an instance. |

The full list lives in the [Python data model docs](https://docs.python.org/3/reference/datamodel.html). We cover the common ones here.

## 2. `__repr__` and `__str__`

`__repr__` should look like a Python expression that *could* re-create the object, or at least be unambiguous and useful in debugging:

```python
class Point:
    def __init__(self, x, y): self.x, self.y = x, y
    def __repr__(self):       return f"Point(x={self.x}, y={self.y})"
```

`__str__` is for end users — what `print()` shows. If you only implement one, implement `__repr__`. Python falls back to `__repr__` from `__str__` but not the other way around.

> **Best practice:** every class you write should have a `__repr__`. The default from `object` is `<point.Point object at 0x10abc>` — useless in logs.

## 3. `__eq__` and `__hash__`

If you implement `__eq__`, Python *automatically* sets `__hash__` to `None`, which makes your instances unhashable (you can't put them in a set or use them as a dict key). To put them back, implement `__hash__` too. The standard recipe is:

```python
class Point:
    def __init__(self, x, y): self.x, self.y = x, y
    def __eq__(self, other):
        return isinstance(other, Point) and self.x == other.x and self.y == other.y
    def __hash__(self):
        return hash((self.x, self.y))
```

For dataclasses, you get `__eq__` for free. If you set `@dataclass(eq=False)`, you opt out. With `frozen=True` you also get `__hash__`.

## 4. Ordering: `__lt__`, `__le__`, `__gt__`, `__ge__`

If you want `<` to work, implement `__lt__`. For the rest, the standard library can synthesize them: `@total_ordering` from `functools` fills in the others given `__eq__` and one ordering method.

```python
from functools import total_ordering

@total_ordering
class Version:
    def __init__(self, n): self.n = n
    def __eq__(self, o):    return self.n == o.n
    def __lt__(self, o):    return self.n < o.n
```

## 5. Operators: `__add__`, `__mul__`, etc.

```python
class Vector:
    def __init__(self, x, y): self.x, self.y = x, y
    def __repr__(self):       return f"Vector({self.x}, {self.y})"
    def __add__(self, other): return Vector(self.x + other.x, self.y + other.y)
    def __mul__(self, k):     return Vector(self.x * k, self.y * k)
```

Three things to know:

- The **right operand** can also define `__radd__` (e.g. `int + Vector`).
- **In-place** versions are `__iadd__`, `__imul__`, etc. (`a += b` calls `a.__iadd__(b)` if defined, else `a = a + b`).
- For "real" numeric types, you'd also implement `__sub__`, `__neg__`, `__truediv__`, etc. The `__add__` example above is a sketch, not a complete numeric tower.

## 6. Iteration: `__iter__` and `__next__`

To make a custom object work in a `for` loop, implement `__iter__` returning an iterator, and `__next__` returning the next value (and raising `StopIteration` when done):

```python
class Countdown:
    def __init__(self, n): self.n = n
    def __iter__(self):    return self            # this object IS the iterator
    def __next__(self):
        if self.n <= 0: raise StopIteration
        self.n -= 1
        return self.n + 1
```

```python
for i in Countdown(3): print(i)        # 3 2 1
```

If your class wraps an existing iterable, `__iter__` can just `return iter(self._items)`.

## 7. Context managers: `__enter__` and `__exit__`

A context manager is an object that sets something up in `__enter__` and tears it down in `__exit__`, regardless of whether the `with` block succeeded or raised:

```python
class Timer:
    def __enter__(self):
        import time
        self._t0 = time.perf_counter()
        return self
    def __exit__(self, exc_type, exc, tb):
        import time
        print(f"elapsed: {time.perf_counter() - self._t0:.3f}s")
        return False                          # don't swallow exceptions
```

For simple cases, the `contextlib.contextmanager` decorator turns a generator into a context manager — easier to read:

```python
from contextlib import contextmanager
import time

@contextmanager
def timer():
    t0 = time.perf_counter()
    yield
    print(f"elapsed: {time.perf_counter() - t0:.3f}s")
```

## 8. Truthiness: `__bool__`

By default, every object is truthy. To make `if obj:` mean something useful, implement `__bool__`:

```python
class Box:
    def __init__(self, items): self.items = items
    def __bool__(self):           return bool(self.items)
```

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code

- [`code/repr_eq.py`](./code/repr_eq.py) — `Point` with a real `__repr__` and `__eq__`/`__hash__`.
- [`code/operators.py`](./code/operators.py) — `Vector` with `+` and `*`.
- [`code/iteration.py`](./code/iteration.py) — `Countdown` iterable and a `paginate` function.
- [`code/context_manager.py`](./code/context_manager.py) — `Timer` as a class and as a `@contextmanager` generator.

## Key terms

dunder method · `__repr__` · `__str__` · `__eq__` · `__hash__` · `__lt__` · `__add__` · `__iter__` · `__next__` · `__enter__` / `__exit__` · `@contextmanager` · `__bool__`

**Next →** [Module 08: Advanced OOP](../08-advanced-oop/)

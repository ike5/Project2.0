# Module 04 — The `__init__` strategy pattern

**Python skill:** storing a *callable* (function or method) in `__init__` so the algorithm is pluggable.
**LeetCode problem:** [1472. Design Browser History](https://leetcode.com/problems/design-browser-history/) · Medium.
**Time:** ~1.5 h.

---

## 1. The pattern

Strategy is the simplest of the "Gang of Four" patterns. The idea: don't hardcode *which* algorithm an object uses — let the caller pick at construction time by passing a function (or another object) into `__init__`.

```python
class TaxCalculator:
    def __init__(self, strategy):
        self.strategy = strategy       # anything callable: (amount) -> tax

    def compute(self, amount):
        return self.strategy(amount)


def flat_rate(amount):
    return amount * 0.15


def progressive(amount):
    return min(amount, 1000) * 0.10 + max(amount - 1000, 0) * 0.20


flat = TaxCalculator(flat_rate)
flat.compute(1500)        # 225.0
```

Three things to notice:

1. The strategy is **any callable**. Function, lambda, method, class with `__call__` — Python doesn't care.
2. The class doesn't know or care *how* the strategy computes. It just calls it.
3. Swapping algorithms is one line: `TaxCalculator(progressive)`.

This is huge in Python because functions are first-class. In Java or C++ you'd define a `Strategy` interface and three classes; in Python you just pass a function.

## 2. Why this matters for LeetCode

Many "Design a Foo" problems give you a constructor with parameters that change behavior. A class that takes a callable in `__init__` is a great fit:

- A "sort" object that takes a `key=` function.
- A "validator" that takes a predicate.
- A "browser history" that takes a strategy for what "back" means (page-by-page, by-domain, etc.).
- A "cache" that takes a `maxsize` and a `policy` (LRU, FIFO, LFU).

Storing the callable on `self` keeps it alive for the lifetime of the object, ready to use in any method.

## 3. The LeetCode problem

> [1472. Design Browser History](https://leetcode.com/problems/design-browser-history/)
>
> You have a **browser** of one tab where you start on the `homepage`, and you can visit another `url`, get back in history `steps` times, get forward in history `steps` times.
>
> Implement `BrowserHistory`:
>
> - `BrowserHistory(homepage)` — visits the page.
> - `visit(url)` — visits a new URL; clears forward history.
> - back(steps)` — move `steps` back in history; return the current url (clamped at the start).
> - `forward(steps)` — move `steps` forward in history; return the current url (clamped at the end).

A list of URLs and an index do it. The "strategy" framing is light here — the class itself is the strategy for "what counts as history". The point is the *API*: a class that takes initial state in `__init__` and mutates it on each call.

## 4. Lambdas and callables

A lambda is just a function without a name:

```python
TaxCalculator(lambda a: a * 0.10).compute(500)   # 50.0
```

You can also pass a `staticmethod` or a bound method:

```python
class Strategies:
    @staticmethod
    def zero(amount):
        return 0.0

TaxCalculator(Strategies.zero).compute(999)   # 0.0
```

And you can pass an instance of any class with `__call__`:

```python
class Greeter:
    def __init__(self, prefix):
        self.prefix = prefix
    def __call__(self, name):
        return f"{self.prefix}, {name}!"

hello = Greeter("Hello")
hello("world")             # 'Hello, world!'
```

But for LeetCode, **a plain function is almost always enough**.

## 5. Anti-patterns

- **Storing a *string* name of a function and dispatching with `if/elif`.** Use a dict or pass the callable directly.
- **Subclassing to change one method.** Composition (passing a callable) usually wins — you don't need a class hierarchy.
- **Putting the algorithm in a class method** when the caller is the only one who knows which algorithm. Move it out.

---

**→ Next: [Module 05 — The subscriber / observer pattern](./../05-observer-pattern/)**

# Solution 09 — Design Patterns

Reference answers. Try first.

## Key points

### Task 1 — `tax.py` (Strategy)

```python
"""A TaxCalculator that delegates to a strategy function.

Run:
    python 09-design-patterns/code/tax.py
"""


def flat_rate(amount: float) -> float:
    return amount * 0.15


def progressive(amount: float) -> float:
    if amount <= 1000:
        return amount * 0.10
    return 1000 * 0.10 + (amount - 1000) * 0.20


class TaxCalculator:
    def __init__(self, strategy) -> None:
        self.strategy = strategy

    def compute(self, amount: float) -> float:
        return self.strategy(amount)


def main() -> None:
    print("flat(1500)      =", TaxCalculator(flat_rate).compute(1500))
    print("progressive(1500) =", TaxCalculator(progressive).compute(1500))


if __name__ == "__main__":
    main()
```

### Task 2 — `newsfeed.py` (Observer)

```python
"""A Newsfeed that broadcasts new headlines to subscribers.

Run:
    python 09-design-patterns/code/newsfeed.py
"""


class Newsfeed:
    def __init__(self) -> None:
        self._headlines: list[str] = []
        self._subscribers: list = []

    def subscribe(self, fn) -> None:
        self._subscribers.append(fn)

    def unsubscribe(self, fn) -> None:
        self._subscribers.remove(fn)

    def add_headline(self, text: str) -> None:
        self._headlines.append(text)
        for fn in list(self._subscribers):
            fn(text)


def main() -> None:
    nf = Newsfeed()

    def printer(text): print(f"  [printer] {text}")

    counter = {"n": 0}
    def counter_fn(text):
        counter["n"] += 1
        print(f"  [counter] total = {counter['n']}")

    nf.subscribe(printer)
    nf.subscribe(counter_fn)

    for h in ("Markets rally", "New product announced", "Earnings beat"):
        nf.add_headline(h)


if __name__ == "__main__":
    main()
```

### Task 3 — `logged.py` (Decorator pattern)

```python
"""A Logger and stacked decorator wrappers.

Run:
    python 09-design-patterns/code/logged.py
"""

from datetime import datetime


class Logger:
    def log(self, msg: str) -> None:
        print(msg)


class UpperLogger:
    def __init__(self, inner: Logger) -> None:
        self.inner = inner

    def log(self, msg: str) -> None:
        self.inner.log(msg.upper())


class TimestampedLogger:
    def __init__(self, inner: Logger) -> None:
        self.inner = inner

    def log(self, msg: str) -> None:
        stamp = datetime.now().isoformat(timespec="seconds")
        self.inner.log(f"[{stamp}] {msg}")


def main() -> None:
    base = Logger()
    print("--- base ---")
    base.log("hi")

    print("--- upper ---")
    UpperLogger(base).log("hi")

    print("--- upper + timestamp ---")
    TimestampedLogger(UpperLogger(base)).log("hi")


if __name__ == "__main__":
    main()
```

### Task 4 — `notifier_factory.py` (Factory)

```python
"""A Notifier hierarchy with a classmethod factory.

Run:
    python 09-design-patterns/code/notifier_factory.py
"""


class Notifier:
    channel: str = "base"

    def send(self, to: str, msg: str) -> None: ...

    @classmethod
    def for_channel(cls, channel: str) -> "Notifier":
        for sub in cls.__subclasses__():
            if sub.channel == channel:
                return sub()
        raise ValueError(f"unknown channel: {channel}")


class EmailNotifier(Notifier):
    channel = "email"
    def send(self, to, msg): print(f"email -> {to}: {msg}")


class SMSNotifier(Notifier):
    channel = "sms"
    def send(self, to, msg): print(f"sms   -> {to}: {msg}")


class PushNotifier(Notifier):
    channel = "push"
    def send(self, to, msg): print(f"push  -> {to}: {msg}")


def main() -> None:
    for ch in ("email", "sms", "push"):
        n = Notifier.for_channel(ch)
        n.send("ana", f"hello via {ch}")


if __name__ == "__main__":
    main()
```

> `cls.__subclasses__()` is a built-in that returns the immediate subclasses of `cls`. It's a quick way to find implementations for a factory. (You can also use the `__init_subclass__` registry from Module 08 for a more explicit approach.)

### Task 5 — `logger_adapter.py` (Adapter)

```python
"""Adapts the built-in `print` to a `log(msg)` method.

Run:
    python 09-design-patterns/code/logger_adapter.py
"""


class PrintLogger:
    """Adapts the print function to a log(msg) interface."""

    def log(self, msg: str) -> None:
        print(msg)


def main() -> None:
    pl = PrintLogger()
    pl.log("hello from the adapter")


if __name__ == "__main__":
    main()
```

## Common pitfalls

- **Naming the GoF Decorator pattern "the same thing as Python's `@decorator`."** They are related (both add behavior) but the GoF one is an *object* that wraps another object; Python's is a higher-order function applied to a function. We'll see the Python decorator syntax more in the next course, but for now: same word, different mechanism.
- **A factory that's just a chain of `if`s.** That's fine for two or three cases. If you have a dozen, use a registry (`__init_subclass__` from Module 08).
- **Forgetting to call `super().__init_subclass__(**kwargs)` in an `Observer`-style base.** A surprising bug that only shows up when you have a longer chain.

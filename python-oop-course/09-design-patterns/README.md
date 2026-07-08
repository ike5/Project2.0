# Module 09 — Design Patterns

**Goal:** Recognize and apply five patterns that come up constantly in OOP code: Strategy, Observer, Decorator, Factory, and Adapter — in *idiomatic* Python. ⏱️ ~3 h · 🎯 Prereq: 08.

---

## 1. What a "design pattern" actually is

A design pattern is a **named, reusable solution to a problem that shows up over and over in object-oriented code.** Patterns aren't rules or libraries — they're shared vocabulary. Once you know the names, you can talk about a design in one sentence instead of five minutes.

This module covers five you'll see in real codebases. For each, we give:

- The problem it solves.
- The structure (who holds what, who calls who).
- A small, runnable example.
- The Pythonic version, because in Python you can often replace a class with a function.

> **Mindset:** a pattern is a tool. Don't apply one just because you learned it. Reach for the simplest design that solves the problem.

## 2. Strategy — swap algorithms at runtime

**Problem:** you have a class that does X one way today, and a different way tomorrow, and you want to switch without rewriting the class.

**Structure:** the *context* holds a reference to a *strategy* object with a known interface; the context delegates the work to it.

```python
from typing import Callable

class Sorter:
    def __init__(self, strategy: Callable[[list], list]):
        self.strategy = strategy

    def sort(self, items): return self.strategy(items)

Sorter(sorted).sort([3, 1, 2])           # ascending
Sorter(lambda xs: list(reversed(sorted(xs)))).sort([3, 1, 2])  # descending
```

In idiomatic Python, the strategy is often just a function. The class is `collections.abc` / `typing.Protocol` if you need a real type.

## 3. Observer — notify dependents of state changes

**Problem:** a *subject* has state that *observers* care about. When the state changes, the observers should be notified — without the subject knowing the concrete types of the observers.

**Structure:** the subject keeps a list of observers (callables) and calls each on change. Observers can subscribe and unsubscribe.

```python
class Subject:
    def __init__(self):
        self._observers = []
        self._value = None

    def subscribe(self, fn): self._observers.append(fn)
    def unsubscribe(self, fn): self._observers.remove(fn)

    @property
    def value(self): return self._value

    @value.setter
    def value(self, v):
        self._value = v
        for fn in list(self._observers):
            fn(v)
```

This is the pattern behind Django signals, asyncio event loops, JS DOM events, and many GUI frameworks.

## 4. Decorator (the pattern) — wrap an object to add behavior

**Problem:** you want to add behavior to a single object — logging, caching, access checks — without touching the object's class or any of its peers.

**Structure:** a wrapper class with the same interface as the wrapped object; each method calls the inner object's method and adds something around it.

```python
class Text:
    def __init__(self, s): self.s = s
    def render(self):       return self.s

class Bold(Text):
    def __init__(self, inner): self.inner = inner
    def render(self):       return f"<b>{self.inner.render()}</b>"

class Italic(Text):
    def __init__(self, inner): self.inner = inner
    def render(self):       return f"<i>{self.inner.render()}</i>"

Bold(Italic(Text("hi"))).render()       # "<b><i>hi</i></b>"
```

This is the **Gang of Four Decorator pattern** — different from Python's `@decorator` syntax (which is a higher-order function applied at *function definition* time).

## 5. Factory — centralize object construction

**Problem:** callers need an object, but you want to hide the construction details — which subclass, what defaults, what cache, what configuration.

**Structure:** a function or method that builds and returns the right thing.

```python
def parser_for(filename: str):
    if filename.endswith(".json"):
        return JSONParser()
    if filename.endswith(".csv"):
        return CSVParser()
    raise ValueError(f"unknown format: {filename}")
```

Sometimes the factory is a classmethod on a base. Sometimes it's just a function. The point is that *the caller doesn't have to know the implementation*.

## 6. Adapter — translate one interface into another

**Problem:** you have an object with the right behavior, but its method names don't match what the rest of your code expects.

**Structure:** a thin wrapper that exposes the expected interface and translates calls to the underlying object.

```python
class CelsiusWeather:
    def temperature_c(self): return 25

class USWeatherAdapter:
    def __init__(self, weather): self.w = weather
    def temperature_f(self):    return self.w.temperature_c() * 9/5 + 32

USWeatherAdapter(CelsiusWeather()).temperature_f()    # 77.0
```

Adapters are everywhere in real code — wrapping a third-party library, an old API, or a different unit system. The pattern is small; the naming is the value.

## 7. A small worked example: a logging Strategy

Put the patterns together. The `Processor` runs steps; the *strategy* is how to log each step. We provide two strategies.

```python
class Processor:
    def __init__(self, logger): self.logger = logger
    def run(self, items):
        for i, x in enumerate(items):
            self.logger(i, x)

class PrintLogger:
    def __call__(self, i, x): print(f"{i}: {x}")

class ListLogger:
    def __init__(self): self.log = []
    def __call__(self, i, x): self.log.append((i, x))

ll = ListLogger()
Processor(ll).run([1, 2, 3])
print(ll.log)
```

`__call__` makes the logger an object you can invoke like a function — Strategy + a touch of Module 07.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code

- [`code/strategy.py`](./code/strategy.py) — `Sorter` with a Strategy function.
- [`code/observer.py`](./code/observer.py) — `Subject` and a couple of observer functions.
- [`code/decorator_pattern.py`](./code/decorator_pattern.py) — `Bold`/`Italic` wrapping a `Text`.
- [`code/factory.py`](./code/factory.py) — `parser_for(filename)` returning the right parser.
- [`code/adapter.py`](./code/adapter.py) — `USWeatherAdapter` translating Celsius to Fahrenheit.

## Key terms

strategy · observer · decorator pattern (GoF) · factory · adapter · callable instance

**Next →** [Module 10: Testing OOP](../10-testing-oop/)

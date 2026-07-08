# Module 06 — Composition

**Goal:** Build classes out of other classes ("has-a"), delegate behavior to inner objects, and use `@dataclass` for value-like objects. ⏱️ ~1.5 h · 🎯 Prereq: 05.

---

## 1. Is-a vs. has-a

Two ways to relate classes:

- **Is-a** = inheritance. `Dog` *is an* `Animal`.
- **Has-a** = composition. `Car` *has an* `Engine`.

The general advice — repeated in design books for decades — is to **prefer composition over inheritance** when you have a choice. Inheritance creates a tight coupling (a subclass *is* the parent, and can be used wherever the parent was, which is a big promise to keep). Composition is a *uses* relationship: `Car` knows about an `Engine`, but the rest of the program doesn't have to.

When is inheritance right?

- A clear is-a relationship ("`Square` is a `Shape`").
- A small, stable hierarchy.
- The Liskov Substitution Principle is satisfied.

When is composition right?

- "Has-a" is a more natural description of the relationship.
- You want to swap parts (a `Car` can have different `Engine`s).
- The "thing" has several responsibilities, each belonging to a different collaborator.

## 2. The composition pattern

```python
class Engine:
    def __init__(self, horsepower: int) -> None:
        self.horsepower = horsepower

    def start(self) -> str:
        return f"engine ({self.horsepower} hp) running"

class Car:
    def __init__(self, make: str, engine: Engine) -> None:
        self.make = make
        self.engine = engine                 # Car has-a Engine

    def start(self) -> str:
        return f"{self.make}: {self.engine.start()}"
```

`Car` doesn't reimplement `start()`. It forwards to `self.engine`. That's the **delegation** pattern: the outer class's method just calls the inner object's method.

You can also build a `Car` *without* supplying an engine — the engine is constructed inside the `Car`:

```python
class Car:
    def __init__(self, make: str) -> None:
        self.make = make
        self.engine = Engine(horsepower=150)
```

The first form is more flexible (you can pass any `Engine`); the second is simpler. Pick based on whether the inner object needs to vary.

## 3. Aggregation (weaker composition)

Sometimes the inner object outlives the outer one. A `Team` has a list of `Player`s, but the `Player`s exist before and after the team. This is **aggregation**. In code, it looks almost identical to composition — it's the lifetime relationship, not the syntax, that differs.

```python
class Team:
    def __init__(self, name: str, players: list["Player"]) -> None:
        self.name = name
        self.players = players               # references, not owned
```

Don't sweat the distinction too much. In Python, both look like "store a reference to another object." What matters is whether the inner object's lifetime is tied to the outer.

## 4. `@dataclass` for value-like objects

A lot of what you'd want a class for is "a bundle of named values" — a 2D point, a config record, a row from a database. Python's `@dataclass` decorator auto-generates `__init__`, `__repr__`, and `__eq__` from your annotations:

```python
from dataclasses import dataclass, field

@dataclass
class Point:
    x: float
    y: float = 0.0
```

That single line is the same as writing a class with an `__init__` that takes `x` and `y`, a `__repr__` like `Point(x=1, y=0.0)`, and an `__eq__` that compares fields.

Key options:

- `@dataclass(frozen=True)` — makes instances immutable (sets `__hash__`, blocks assignment). Great for values.
- `@dataclass(eq=False)` — skip the auto-`__eq__` (and `__hash__`).
- `field(default_factory=list)` — for mutable defaults.

```python
@dataclass
class Player:
    name: str
    inventory: list[str] = field(default_factory=list)
```

> **Why not use a dict or `NamedTuple`?** A `dataclass` is the right answer when the bundle has *behavior* in addition to data — methods, invariants, validation. For pure records, `typing.NamedTuple` is also fine and slightly faster.

## 5. Mixing composition and dataclass

Dataclasses can hold other dataclasses. This is one of the most pleasant ways to model small domain objects:

```python
@dataclass(frozen=True)
class Money:
    amount: int                              # cents
    currency: str = "USD"

@dataclass
class Order:
    id: int
    items: list[str] = field(default_factory=list)
    total: Money = field(default_factory=lambda: Money(0))
```

## 6. When to use what

| Use | When |
|---|---|
| A plain class | You have state + behavior + invariants (validation in `__init__`). |
| A `@dataclass` | You mostly have a bundle of named values; behavior is minor. |
| A `NamedTuple` | Pure data, immutable, small. |
| Inheritance | A clear is-a relationship; the Liskov rule is satisfied. |
| Composition | "Has-a" — the new class is built out of other classes. |

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code

- [`code/car_engine.py`](./code/car_engine.py) — `Car` composes an `Engine` and delegates.
- [`code/dataclass_demo.py`](./code/dataclass_demo.py) — `Point`, `Money`, and `Order` as dataclasses.
- [`code/composition_vs_inheritance.py`](./code/composition_vs_inheritance.py) — the same domain modeled both ways, to feel the difference.

## Key terms

composition · delegation · aggregation · `@dataclass` · `frozen=True` · `default_factory` · is-a vs. has-a

**Next →** [Module 07: Magic Methods](../07-magic-methods/)

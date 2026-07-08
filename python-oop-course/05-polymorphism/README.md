# Module 05 — Polymorphism

**Goal:** Write one piece of code that works on many kinds of objects, and use Python's three tools for saying what "kind of" means: duck typing, abstract base classes, and `Protocol`. ⏱️ ~2 h · 🎯 Prereq: 04.

---

## 1. The core idea, in one sentence

**Polymorphism** is the property that one piece of code can work on objects of different types, as long as they expose the right method. The caller doesn't need to know what the object is — only what it can do.

```python
def announce(speaker):
    print(speaker.greet())                  # works for any object with .greet()
```

The classic shapes example:

```python
shapes = [Square(2), Circle(3), Triangle(3, 4, 5)]
for shape in shapes:
    print("area:", shape.area())            # each shape computes its own
```

No `isinstance` chain. No `match` on type. Just call `area()` and trust that the object knows what to do.

## 2. Duck typing — Python's default

"If it walks like a duck and quacks like a duck, it's a duck." Python doesn't check types before calling methods; it just calls them. If the object has the method, it works. If it doesn't, you get `AttributeError`.

```python
class Duck:
    def quack(self): return "quack!"

class Person:
    def quack(self): return "I'm pretending to be a duck"

def make_it_quack(thing):
    return thing.quack()                    # works for both
```

Duck typing is the *default* in Python. You don't opt in; it's the style. Most of the time, that's exactly what you want.

> **When duck typing bites:** when you have a large, long-lived codebase and you want a *static* guarantee that a function's argument really does have the right method. For that, use `typing.Protocol` (see below) or run a type checker like `mypy`.

## 3. Abstract base classes — saying "you must implement this"

Sometimes you want to *force* subclasses to implement a method. That's what an **abstract base class (ABC)** is for. The `@abstractmethod` decorator marks a method that subclasses *must* override; you can't instantiate the ABC directly.

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...
    @abstractmethod
    def perimeter(self) -> float: ...
```

```python
class Square(Shape):
    def __init__(self, side: float) -> None: self.side = side
    def area(self) -> float:      return self.side ** 2
    def perimeter(self) -> float: return 4 * self.side
```

```python
Shape()                            # TypeError: Can't instantiate abstract class Shape
Square(2).area()                   # 4
```

ABCs are great when:

- You have a small, fixed set of related classes (the standard library's `collections.abc` is built on them).
- You want a clear, runtime-enforced contract.
- You're writing a framework and you want to make sure plugins implement the right methods.

They're overkill when:

- You only have two or three classes that already work.
- You want the "shape" to be implied by behavior, not enforced by inheritance.

## 4. `Protocol` — structural typing, no inheritance

`typing.Protocol` describes what methods an object *should* have, without requiring it to inherit from a specific class. This is **structural typing** (also called "static duck typing"). A class qualifies if it has the methods, regardless of its actual base.

```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None: ...

def render(obj: Drawable) -> None:
    obj.draw()
```

`render` accepts any object that has a `draw()` method. It doesn't need to inherit from `Drawable`. With a type checker (`mypy`, `pyright`), this is checked at *type-check time*; at *runtime* it's still just a regular function — Python doesn't enforce protocols at runtime by default.

> **Tip:** prefer `Protocol` over ABCs when you don't want to force inheritance. Reach for ABCs when you also want runtime checks (e.g. you want to be sure plugins implement the right methods without running a type checker).

## 5. Operator overloading as polymorphism

When you write `a + b` and `a` is a custom class, Python calls `a.__add__(b)`. That's polymorphism in action: the same `+` operator works on ints, strings, lists, *and* your own classes — as long as they implement `__add__`. Module 07 covers the dunder methods in detail; for now just know this is the same idea in a different costume.

## 6. Liskov Substitution Principle (a one-paragraph version)

A `Square` that inherits from `Rectangle` is a classic violation. A `Square` *is a* `Rectangle` mathematically, but if `Rectangle.set_width` and `Rectangle.set_height` exist independently, `Square` can't implement both. Code that uses `Rectangle` polymorphically will break when handed a `Square`.

The general rule: **a subclass should be usable anywhere its parent was expected, without surprises.** If your subclass has to throw away or weaken the parent's guarantees, you probably want composition (Module 06), not inheritance.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code

- [`code/duck_typing.py`](./code/duck_typing.py) — two unrelated classes that both have `.quack()`, and a function that takes "anything."
- [`code/abstract_shape.py`](./code/abstract_shape.py) — `Shape` ABC and three concrete shapes.
- [`code/protocol_render.py`](./code/protocol_render.py) — a `Drawable` Protocol and three classes that don't share a base, but all `draw()`.

## Key terms

polymorphism · duck typing · abstract base class · `ABC` · `@abstractmethod` · `Protocol` · structural typing · Liskov Substitution Principle

**Next →** [Module 06: Composition](../06-composition/)

# Python OOP Cheatsheet

A one-page reference for class syntax, the most useful dunder methods, and the patterns taught in this course. Keep it open in a second tab while you work.

## Class basics

```python
class Dog:
    species = "Canis familiaris"          # class attribute (shared)

    def __init__(self, name: str, age: int) -> None:
        self.name = name                  # instance attribute (per object)
        self.age = age

    def bark(self) -> str:                # instance method
        return f"{self.name}: woof!"

    @classmethod
    def from_birth_year(cls, name, year):  # alternative constructor
        return cls(name, 2025 - year)

    @staticmethod
    def is_old(age):                      # utility; no self/cls
        return age >= 10

d = Dog("Rex", 4)
Dog("Buddy", 3).bark()                    # "Buddy: woof!"
Dog.from_birth_year("Pip", 2021)
```

## Encapsulation & properties

```python
class Account:
    def __init__(self, owner: str, balance: float) -> None:
        self.owner = owner
        self._balance = balance            # _single: "internal, don't touch"

    @property
    def balance(self) -> float:           # read-only
        return self._balance

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("must be positive")
        self._balance += amount

a = Account("Ana", 100)
a.balance                                 # 100
a.balance = 200                           # AttributeError
```

```python
class Celsius:
    def __init__(self, temp: float) -> None:
        self._temp = temp

    @property
    def temp(self) -> float:
        return self._temp

    @temp.setter
    def temp(self, value: float) -> None:
        if value < -273.15:
            raise ValueError("below absolute zero")
        self._temp = value
```

## Inheritance & `super()`

```python
class Animal:
    def __init__(self, name: str) -> None:
        self.name = name

    def speak(self) -> str:
        return "..."

class Dog(Animal):
    def __init__(self, name: str, breed: str) -> None:
        super().__init__(name)            # call parent __init__
        self.breed = breed

    def speak(self) -> str:               # override
        return f"{self.name}: woof"

Dog("Rex", "lab").speak()                 # "Rex: woof"
isinstance(Dog("Rex", "lab"), Animal)     # True
Dog.mro()                                 # [<class 'Dog'>, <class 'Animal'>, <class 'object'>]
```

## Abstract base classes

```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

    @abstractmethod
    def perimeter(self) -> float: ...

class Square(Shape):
    def __init__(self, side: float) -> None:
        self.side = side
    def area(self):      return self.side ** 2
    def perimeter(self): return 4 * self.side

Shape()                                   # TypeError: can't instantiate ABC
```

## Protocols (structural typing)

```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None: ...

def render(obj: Drawable) -> None:
    obj.draw()                            # works for any class with .draw()
```

## Composition

```python
class Engine:
    def start(self) -> str: return "vroom"

class Car:                                # Car HAS-A Engine
    def __init__(self) -> None:
        self.engine = Engine()            # own it

    def start(self) -> str:
        return self.engine.start()
```

## Dataclasses

```python
from dataclasses import dataclass, field

@dataclass
class Point:
    x: float
    y: float = 0.0

@dataclass(frozen=True)
class FrozenPoint:
    x: float
    y: float

@dataclass
class Player:
    name: str
    inventory: list[str] = field(default_factory=list)
```

## Magic methods

```python
class Vector:
    def __init__(self, x, y): self.x, self.y = x, y

    def __repr__(self):  return f"Vector({self.x!r}, {self.y!r})"
    def __str__(self):   return f"({self.x}, {self.y})"
    def __eq__(self, o):  return isinstance(o, Vector) and (self.x, self.y) == (o.x, o.y)
    def __hash__(self):  return hash((self.x, self.y))
    def __add__(self, o):return Vector(self.x + o.x, self.y + o.y)
    def __len__(self):   return 2
    def __bool__(self):  return self.x or self.y
    def __iter__(self):  yield from (self.x, self.y)
```

## Context managers

```python
class managed_file:
    def __init__(self, path): self.path = path
    def __enter__(self):
        self.f = open(self.path)
        return self.f
    def __exit__(self, *exc):
        self.f.close()

with managed_file("a.txt") as f:
    f.read()
```

```python
from contextlib import contextmanager

@contextmanager
def timer():
    import time
    t0 = time.perf_counter()
    yield
    print(f"elapsed: {time.perf_counter() - t0:.3f}s")
```

## Iteration

```python
class Countdown:
    def __init__(self, n): self.n = n
    def __iter__(self):   return self
    def __next__(self):
        if self.n <= 0: raise StopIteration
        self.n -= 1
        return self.n + 1

for i in Countdown(3): print(i)           # 3 2 1
```

## `__slots__`

```python
class Point:
    __slots__ = ("x", "y")
    def __init__(self, x, y): self.x, self.y = x, y

p = Point(1, 2)
p.z = 3                                  # AttributeError
```

## Descriptors (the property mechanism, manual)

```python
class Positive:
    def __set_name__(self, owner, name): self._name = "_" + name
    def __get__(self, obj, owner):       return getattr(obj, self._name, None)
    def __set__(self, obj, value):
        if value < 0: raise ValueError("must be >= 0")
        setattr(obj, self._name, value)

class Account:
    balance = Positive()
```

## Decorator pattern

```python
class Text:
    def render(self) -> str: return "hello"

class Bold(Text):
    def __init__(self, inner: Text) -> None: self.inner = inner
    def render(self) -> str: return f"<b>{self.inner.render()}</b>"
```

## Strategy pattern

```python
class Sorter:
    def __init__(self, strategy): self.strategy = strategy
    def sort(self, items):    return self.strategy(items)

Sorter(sorted).sort([3, 1, 2])            # uses builtin sorted
Sorter(lambda xs: list(reversed(sorted(xs)))).sort([3, 1, 2])
```

## pytest essentials

```python
# test_account.py
from bank import Account

def test_deposit_increases_balance():
    a = Account("Ana", 0)
    a.deposit(50)
    assert a.balance == 50

def test_negative_deposit_raises():
    import pytest
    with pytest.raises(ValueError):
        Account("Ana", 0).deposit(-1)
```

```bash
pytest -q                 # quiet run
pytest --cov=bank         # coverage
```

## Gotchas

- **`self` is not a keyword.** It's a convention. Don't name your first parameter `this` or `me`.
- **Don't call `self.__init__` directly** on an instance to "re-init" it. Create a new one.
- **Class attributes are shared.** A mutable class attribute (e.g. `tags = []`) is shared by every instance and is a classic bug source. Use `default_factory` from `dataclasses` instead.
- **`super()` always uses the MRO.** In multiple inheritance, you may want to call a sibling's method via `super(SubClass, self).method()`.
- **Properties and `__slots__` together require care.** `__slots__` doesn't reserve space for properties — you have to give the property a class-level storage name.
- **Dataclasses don't set up parents' `__init__`.** If you inherit from a non-dataclass, write `__init__` yourself or use `kw_only` carefully.
- **Don't over-OOP.** A two-function script doesn't need a class. Reach for OOP when you have state + behavior + identity.

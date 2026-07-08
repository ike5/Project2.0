# Module 02 — Classes & Objects

**Goal:** Write your own classes with `__init__`, `self`, instance and class attributes, and methods that read and mutate state. ⏱️ ~2 h · 🎯 Prereq: 01.

---

## 1. The shape of a class

The minimum useful class has three pieces:

1. The `class` keyword and a name.
2. An `__init__` method that sets up the new instance.
3. One or more methods that read or modify the instance.

```python
class Counter:
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1

    def reset(self):
        self.value = 0
```

A few rules of the road:

- Class names are **CapitalizedWords** (PEP 8). `Counter`, not `counter`.
- The first parameter of every instance method is `self`. It is the instance the method is called on.
- Inside a method, `self.value = 0` creates an *instance attribute*. It belongs to *this* instance, not the class.

## 2. `self` is not magic — it's just a parameter

When you call `c.increment()`, Python turns that into `Counter.increment(c)`. The `self` parameter is the instance. You can confirm this:

```python
c = Counter()
c.increment()
Counter.increment(c)          # same call, different spelling
```

That little fact is the key to understanding the rest of the course. Methods are functions; `self` is what binds them to instances.

> **Note:** `self` is convention, not a keyword. The code works if you name it `this` or `me`. Don't. The linter will complain and so will your teammates.

## 3. Instance attributes vs. class attributes

Attributes declared inside `__init__` (or assigned to `self` anywhere) are **instance attributes** — each instance has its own copy. Attributes declared directly in the class body (outside any method) are **class attributes** — shared by every instance.

```python
class Dog:
    species = "Canis familiaris"     # class attribute

    def __init__(self, name):
        self.name = name             # instance attribute
```

```python
>>> d = Dog("Rex")
>>> d.name                          # instance: own
'Canis familiaris'                  # wait — that's species
>>> d.name
'Rex'
>>> d.species                       # class: shared
'Canis familiaris'
>>> Dog.species                     # also accessible on the class
'Canis familiaris'
```

The big gotcha: **a mutable class attribute is shared by every instance**. If you write `class Bag: items = []` and every bag appends to `self.items`, they all see each other's items. We'll see this in the lab.

> **Best practice:** treat class attributes as read-only constants. For mutable defaults, use `None` and create the container in `__init__`, or use `@dataclass(field(default_factory=list))` (Module 06).

## 4. Methods that do work: mutating vs. returning

There are two flavors of method:

- **Mutators** change the instance's state. By convention they return `None` (don't write `return self.value`).
- **Accessors / queries** return a value computed from the instance's state and don't change it.

```python
class Counter:
    def increment(self) -> None:    # mutator
        self.value += 1

    def current(self) -> int:       # accessor
        return self.value
```

Mixing the two is fine, but the convention is: mutators return `None`, accessors return a value. Tools and linters rely on this.

## 5. Adding methods: a worked example

Let's grow `Dog` into something more useful. Each new method shows a different thing methods can do — return values, take parameters, mutate state.

```python
class Dog:
    species = "Canis familiaris"

    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age

    def bark(self) -> str:                       # returns a string
        return f"{self.name}: woof!"

    def have_birthday(self) -> None:             # mutates self
        self.age += 1

    def is_puppy(self) -> bool:                  # pure read of state
        return self.age < 2

    def greet(self, other: "Dog") -> str:        # takes another instance
        return f"{self.name} sniffs {other.name}"
```

`greet` is interesting: it takes *another `Dog`*. Methods can take whatever they need, including other instances of the same class.

## 6. Constructors that do more: validation

`__init__` is the right place to reject bad input. The convention is to raise an exception (often `ValueError` or `TypeError`) rather than silently accepting garbage.

```python
class Dog:
    def __init__(self, name: str, age: int) -> None:
        if not name:
            raise ValueError("name must be non-empty")
        if age < 0:
            raise ValueError("age must be >= 0")
        self.name = name
        self.age = age
```

The class of object you build is much easier to reason about if invalid states are impossible to construct.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code

- [`code/counter.py`](./code/counter.py) — a `Counter` class you can instantiate, increment, reset, and read.
- [`code/dog_methods.py`](./code/dog_methods.py) — the worked `Dog` example with the five methods.
- [`code/class_vs_instance_attr.py`](./code/class_vs_instance_attr.py) — shows the mutable-class-attribute trap and how to avoid it.

## Key terms

class · instance · `__init__` · `self` · instance attribute · class attribute · mutator · accessor

**Next →** [Module 03: Encapsulation](../03-encapsulation/)

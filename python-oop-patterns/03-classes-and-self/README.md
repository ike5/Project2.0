# Module 03 — Classes & `self`

**Python skill:** defining a class, `__init__`, `self`, instance vs class state — the smallest unit of OOP on LeetCode.
**LeetCode problem:** [1603. Design Parking System](https://leetcode.com/problems/design-parking-system/) · Easy.
**Time:** ~1.5 h.

---

## 1. The smallest useful class

A class is a blueprint for an object. The object holds *state* (data) and exposes *behavior* (methods):

```python
class ParkingSystem:
    def __init__(self, big: int, medium: int, small: int) -> None:
        self.slots = [big, medium, small]   # index by carType-1

    def addCar(self, carType: int) -> bool:
        if self.slots[carType - 1] == 0:
            return False
        self.slots[carType - 1] -= 1
        return True
```

Three things to internalize:

1. **`__init__`** is the constructor. It runs when you write `ParkingSystem(1, 1, 0)`.
2. **`self`** is the *current instance*. Python passes it in for you; you don't include it in the call.
3. **State lives on `self`.** Each `ParkingSystem` instance has its own `slots` list.

## 2. `self`, more carefully

When you write:

```python
ps = ParkingSystem(1, 1, 0)
ps.addCar(1)
```

Python roughly does:

```python
ParkingSystem.__init__(ps, 1, 1, 0)
ParkingSystem.addCar(ps, 1)
```

The instance (`ps`) is the *first* argument to the method, bound to the name `self` inside the body. That's why you write `self.slots` and not `slots` — you need to say *whose* `slots`.

**Anti-pattern:** writing `self` in the call site:

```python
ps.self.addCar(1)    # AttributeError
ps.addCar(self, 1)   # TypeError
```

Don't do either.

## 3. Instance attributes vs class attributes

An *instance* attribute is set on `self` in `__init__` (or anywhere via `self.x = ...`). Each instance has its own copy.

A *class* attribute is set in the class body. It's shared by all instances:

```python
class Counter:
    count = 0                          # class attribute

    def __init__(self) -> None:
        Counter.count += 1
        self.id = Counter.count        # instance attribute
```

On LeetCode, you almost always want instance attributes. Class attributes are for things that are *truly* shared (constants, registries, counters that aren't per-object).

## 4. The LeetCode problem

> [1603. Design Parking System](https://leetcode.com/problems/design-parking-system/)
>
> Design a parking system for a parking lot. The lot has three kinds of parking spaces: big, medium, and small, with a fixed number of slots for each. Implement:
>
> - `ParkingSystem(big, medium, small)` — constructor.
> - `addCar(carType)` — checks if a slot of that type is available; if so, takes it and returns `True`; otherwise returns `False`. `carType` is `1` (big), `2` (medium), or `3` (small).

The implementation is *literally* the four-line class above. The lesson here isn't the algorithm — it's the API design and the habit of reaching for a class when the problem says "design a …".

## 5. When to use a class on LeetCode

You don't need a class for everything. The rule of thumb:

- **"Design a Foo that does X, Y, Z"** → class. There are multiple operations and shared state.
- **"Given an array, return …"** → function. There's one operation, no shared state across calls.
- **"Implement a … iterator"** → class. State is what makes iteration work.
- **"Design a … cache"** → class. State is the cache.

A class without state is usually a sign you want a function (or a `@staticmethod`). A class with one method that does everything is a sign you want a function.

---

**→ Next: [Module 04 — The `__init__` strategy pattern](./../04-strategy-pattern/)**

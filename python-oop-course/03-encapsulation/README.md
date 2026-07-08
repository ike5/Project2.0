# Module 03 — Encapsulation

**Goal:** Control how the outside world touches a class's data: the `_private` and `__mangled` conventions, `@property` getters/setters, and read-only state. ⏱️ ~1.5 h · 🎯 Prereq: 02.

---

## 1. What "encapsulation" means in Python

Encapsulation is the practice of **putting data and the code that operates on it in one unit, and deciding how much of that data the rest of the program is allowed to touch directly.**

Languages like Java and C# have keywords (`private`, `protected`) that the compiler enforces. Python has none of that. The language gives you **conventions** plus a tiny amount of name-mangling magic, and trusts you to use them.

The levels, in order of strength:

| What you write | What it means |
|---|---|
| `self.value` | Public. Anyone can read and write. The default. |
| `self._value` | "Protected" by convention. Don't touch from outside. Python doesn't enforce this; your team does. |
| `self.__value` | Name-mangled to `self._ClassName__value`. Harder to reach into, but **not secure**. Don't use for real secrets. |
| `@property` | A method that *looks* like an attribute. Lets you add validation or computation without changing the public interface. |

> **Note:** there's no equivalent of `private final` in pure Python. If you need a value that genuinely can't change, use a `tuple`, a `frozenset`, a frozen `@dataclass` (Module 06), or just write a property with no setter.

## 2. The `_single_leading_underscore` convention

The single underscore is the most common way to say "this is internal." Python's standard library is full of it: `collections.OrderedDict` had an `_OrderedDict__root` style attribute once, and many modules use `_helper()` for private functions.

```python
class Stack:
    def __init__(self):
        self._items = []                     # "internal — don't touch"

    def push(self, item):
        self._items.append(item)

    def pop(self):
        return self._items.pop()
```

Nothing stops a determined caller from doing `s._items.append("nope")`. The convention is the only enforcement. **Linters and reviewers will flag this in code review.** That's the point.

## 3. The `__double_leading_underscore` name-mangling

A name with two leading underscores (and at most one trailing underscore) inside a class body is **mangled** to `_ClassName__name`. The reason isn't security — it's to avoid *accidental* attribute clashes when a subclass defines an attribute with the same name.

```python
class Account:
    def __init__(self):
        self.__balance = 0
```

```python
>>> a = Account()
>>> a.__balance
AttributeError: 'Account' object has no attribute '__balance'
>>> a._Account__balance
0
```

Mangling is mostly useful when you write a base class meant to be subclassed and you want to be sure a subclass doesn't *accidentally* override an internal name. It is **not** a privacy mechanism. Don't use it for "private" things; use `_name`.

> **Gotcha:** names that start and end with `__` (like `__init__`, `__repr__`) are *dunder methods* — Python's hooks. **Do not name your own attributes that way**, or you'll break things in surprising ways.

## 4. The `@property` decorator — the Pythonic getter

The whole point of `@property` is to let you start with a plain attribute and *upgrade* it to a method without breaking the call sites. The classic example:

```python
class Circle:
    def __init__(self, radius: float) -> None:
        self.radius = radius

    @property
    def area(self) -> float:                  # used as c.area, not c.area()
        return 3.14159 * self.radius ** 2
```

`c.area` looks like an attribute but is recomputed on every access. The caller never has to know.

A property can also define a **setter**:

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

`@temp.setter` is just a decorator Python knows about because `temp` was previously decorated with `@property`. The getter and setter must have the same name.

A property with only a getter is **read-only**. Assigning to it raises `AttributeError`. That's the right answer for "computed value the outside world shouldn't set."

## 5. When to use a property vs. an attribute

Default: use a plain attribute. Add a property when:

- You need to *validate* the value being set.
- The "value" is *computed* from other state (like `area` from `radius`).
- You need *side effects* on read or write (logging, cache invalidation, etc.).
- You start with a plain attribute and later need to upgrade it without breaking callers.

Don't use a property when:

- The "computation" is expensive and the value is requested rarely (use a method).
- The result isn't really state — like `c.diameter()` is fine as a method, it doesn't have to be a property.

## 6. Putting it together: a `BankAccount` v2

```python
class BankAccount:
    def __init__(self, owner: str, balance: float = 0) -> None:
        self.owner = owner
        self._balance = 0
        self.balance = balance               # use the setter for validation

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if value < 0:
            raise ValueError("balance must be >= 0")
        self._balance = value
```

The clever bit is that `self.balance = balance` in `__init__` runs the *setter*, so the negative-balance check fires on construction. This pattern — assigning through the property to validate — is idiomatic.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code

- [`code/encapsulation_levels.py`](./code/encapsulation_levels.py) — runs through the public / `_` / `__` levels and prints the surprises.
- [`code/property_demo.py`](./code/property_demo.py) — `Circle` (computed) and `Celsius` (validated) properties, plus a read-only one.
- [`code/bank_account_v2.py`](./code/bank_account_v2.py) — the validated `BankAccount` from this README.

## Key terms

encapsulation · `_protected` · `__name` mangling · `@property` · `@x.setter` · read-only attribute

**Next →** [Module 04: Inheritance](../04-inheritance/)

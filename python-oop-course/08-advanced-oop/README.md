# Module 08 — Advanced OOP

**Goal:** Use `__slots__`, descriptors, `classmethod`/`staticmethod`, `__init_subclass__`, and a peek at metaclasses — the things you only need in the corners of real code. ⏱️ ~2 h · 🎯 Prereq: 07.

---

## 1. `__slots__`: lock down the attribute set

By default, every Python object has a `__dict__` that lets you add arbitrary attributes. That's flexible, but it costs memory and means typos like `obj.nmae` silently create new attributes. `__slots__` is a class-level tuple that fixes the set of allowed attributes:

```python
class Point:
    __slots__ = ("x", "y")
    def __init__(self, x, y): self.x, self.y = x, y
```

```python
p = Point(1, 2)
p.z = 3          # AttributeError
```

Per-instance memory savings are real for large numbers of small objects. The trade-off: no `__dict__`, less flexibility, and you must redeclare parent slots in subclasses.

> **When to use `__slots__`:** tight inner-loop classes with many instances, value-like types where you want a fixed shape. **When not to:** most ordinary classes — the flexibility is worth the bytes.

## 2. `@staticmethod` and `@classmethod`

Three kinds of methods live in a class body:

- **Instance method** — gets `self`. The default.
- **Class method** — gets `cls` (the class itself). Often used for alternative constructors.
- **Static method** — gets neither. Just a function that happens to live in the class namespace.

```python
class Date:
    def __init__(self, y, m, d): self.y, self.m, self.d = y, m, d

    @classmethod
    def from_string(cls, s):                     # alternative constructor
        y, m, d = map(int, s.split("-"))
        return cls(y, m, d)

    @staticmethod
    def is_leap(year):                           # pure utility
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
```

`Date.from_string("2026-07-07")` returns a `Date`. `Date.is_leap(2024)` is a plain function call. Use `@staticmethod` sparingly; often a free function is clearer.

## 3. Descriptors: the engine behind `property`

A **descriptor** is an object that defines `__get__`, `__set__`, or `__delete__`. The `@property` decorator builds one. Methods themselves are descriptors. Understanding descriptors helps you write reusable validation/lookup logic.

The minimum:

```python
class Positive:
    def __set_name__(self, owner, name):
        self._name = "_" + name                # the backing storage

    def __get__(self, obj, owner):
        if obj is None: return self
        return getattr(obj, self._name, None)

    def __set__(self, obj, value):
        if value < 0:
            raise ValueError("must be >= 0")
        setattr(obj, self._name, value)


class Account:
    balance = Positive()                        # descriptor instance
    def __init__(self, balance):
        self.balance = balance
```

`__set_name__` is a Python 3.6+ hook: the descriptor learns the attribute name it's been bound to (`"balance"`) at class-creation time, so it can pick its own storage name.

You can use this pattern to build a dozen fields of validation without writing twelve property blocks.

## 4. `__init_subclass__`: hook into subclass creation

`__init_subclass__` is a class method on the *base* that gets called every time a subclass is *defined*. It lets you customize subclass creation without writing a metaclass.

```python
class Plugin:
    plugins = {}

    def __init_subclass__(cls, *, name, **kwargs):
        super().__init_subclass__(**kwargs)
        Plugin.plugins[name] = cls


@Plugin.register(name="csv")                    # syntactic sugar
class CSVPlugin(Plugin):
    pass

@Plugin.register(name="json")
class JSONPlugin(Plugin):
    pass

Plugin.plugins                                 # {'csv': CSVPlugin, 'json': JSONPlugin}
```

This is how many plugin systems (e.g. setuptools entry points, ORMs) work under the hood. It's more powerful than a registry you build by hand, because it runs at *class definition* time.

## 5. A peek at metaclasses

A **metaclass** is the class of a class. By default, classes are instances of `type`. You can subclass `type` to customize class creation:

```python
class Tagged(type):
    def __new__(mcs, name, bases, namespace, *, tag):
        namespace["_tag"] = tag
        return super().__new__(mcs, name, bases, namespace)

class Animal(metaclass=Tagged, tag="living"):
    pass
```

`Animal._tag` is now `"living"`. Every subclass of `Animal` will also have `_tag = "living"`.

> **Reality check:** you almost never need a custom metaclass. `__init_subclass__` and class decorators cover 95% of use cases. Reach for a metaclass only when you need to control the *class object itself* (its `__dict__`, its MRO construction, its very creation).

## 6. A short catalog of "things you may not need today"

- **`__set_name__`** — descriptor hook for the attribute name.
- **`__class_getitem__`** — supports `MyClass[int]` syntax (used by `dataclass`-like libraries).
- **`__del__`** — destructor; rarely used, because Python's garbage collector handles cleanup.
- **`__instancecheck__` / `__subclasscheck__`** — control `isinstance` and `issubclass`; what makes `numbers.Number` and friends work.
- **`__getattr__` / `__getattribute__`** — intercept attribute access; powerful, easy to misuse.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code

- [`code/slots_demo.py`](./code/slots_demo.py) — a `__slots__` class that rejects new attributes.
- [`code/class_static_methods.py`](./code/class_static_methods.py) — `Date` with a `from_string` classmethod and `is_leap` staticmethod.
- [`code/descriptor_validation.py`](./code/descriptor_validation.py) — the `Positive` descriptor applied to several fields.
- [`code/init_subclass_plugin.py`](./code/init_subclass_plugin.py) — a tiny plugin registry built with `__init_subclass__`.

## Key terms

`__slots__` · `@staticmethod` · `@classmethod` · descriptor · `__set_name__` · `__init_subclass__` · metaclass

**Next →** [Module 09: Design Patterns](../09-design-patterns/)

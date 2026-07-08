# Module 04 — Inheritance

**Goal:** Inherit from a base class, override methods, call `super()`, and read the MRO when something surprises you. ⏱️ ~2 h · 🎯 Prereq: 03.

---

## 1. The single-inheritance shape

Inheritance lets a new class **reuse and extend** an existing one. The existing class is the *base* (or *parent*, *superclass*); the new one is the *derived* (or *child*, *subclass*).

```python
class Animal:
    def __init__(self, name: str) -> None:
        self.name = name

    def speak(self) -> str:
        return "..."

class Dog(Animal):
    pass                                       # Dog inherits everything from Animal

rex = Dog("Rex")
rex.speak()                                    # "..."
```

Even an empty subclass gets every method and attribute the parent has. The `pass` body is legal Python for "no additions."

## 2. Overriding methods

To change a parent's behavior, define a method with the same name in the child. The child's version wins.

```python
class Dog(Animal):
    def speak(self) -> str:
        return f"{self.name}: woof!"
```

This is called **overriding**. It's the most common thing you'll do in a subclass.

## 3. `super()` — calling the parent's version

Often you want to *extend* the parent's behavior, not replace it. `super()` returns a proxy that looks up methods on the parent classes. Use it in `__init__` to call the parent's initializer, and in overridden methods to call the parent's version.

```python
class Dog(Animal):
    def __init__(self, name: str, breed: str) -> None:
        super().__init__(name)                 # let Animal set self.name
        self.breed = breed                     # Dog-specific setup

    def speak(self) -> str:
        parent_voice = super().speak()         # "...", if you want it
        return f"{self.name}: woof! ({parent_voice})"
```

The `super()` call is the single most important pattern in inheritance. **Always call `super().__init__()` from a subclass `__init__`** — even if you think you don't need to. It saves you later.

> **Note:** `super()` doesn't always mean "the parent class." In multiple inheritance, it means "the next class in the MRO." We'll see that shortly.

## 4. The MRO — method resolution order

When you do `obj.method()`, Python searches a fixed order of classes:

1. The instance's class.
2. Its base class.
3. Its base's base class.
4. …all the way up to `object`.

The order is computed once, deterministically, by an algorithm called **C3 linearization**. You can read it with `ClassName.mro()` or `ClassName.__mro__`:

```python
>>> Dog.mro()
[<class '__main__.Dog'>, <class '__main__.Animal'>, <class 'object'>]
```

For most single-inheritance code, you never need to think about the MRO. The moment you see surprising behavior, `mro()` is the first thing to check.

## 5. `isinstance` and `issubclass`

Two built-ins that go hand-in-hand with inheritance:

- `isinstance(obj, Class)` — True if `obj` is an instance of `Class` *or any of its subclasses*.
- `issubclass(Sub, Parent)` — True if `Sub` is a subclass of `Parent`.

```python
isinstance(rex, Dog)         # True
isinstance(rex, Animal)      # True (Dog inherits from Animal)
isinstance(rex, object)      # True (every class inherits from object)
issubclass(Dog, Animal)      # True
```

> **Tip:** prefer `isinstance` over `type(x) is Class` for the same reason — it keeps working when subclasses show up.

## 6. When to use inheritance (and when not to)

Reach for inheritance when the relationship really is **"is-a"**: a `Dog` *is an* `Animal`; a `Square` *is a* `Shape`. The subclass should be usable everywhere the parent was.

Don't use inheritance when the relationship is **"has-a"**: a `Car` *has an* `Engine`; a `Playlist` *has* `Song` objects. That's composition, which is Module 06. A common mistake: making a `Square` inherit from `Rectangle` (or vice versa) just to save typing — it almost always bites later.

Rule of thumb: **prefer composition over inheritance** unless you have a clear, tested is-a relationship.

## 7. A small inheritance chain

```python
class Animal:
    def __init__(self, name: str) -> None:
        self.name = name
    def speak(self) -> str: return "..."

class Dog(Animal):
    def speak(self) -> str: return f"{self.name}: woof!"

class Puppy(Dog):
    def speak(self) -> str:
        return super().speak().replace("woof", "yip")
```

`Puppy("Rex")` ends up with MRO `[Puppy, Dog, Animal, object]`. Calling `puppy.speak()` runs `Puppy.speak`, which calls `Dog.speak` (via `super()`), which doesn't call further up — and you get `"Rex: yip!"`.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code

- [`code/basic_inheritance.py`](./code/basic_inheritance.py) — `Animal` / `Dog` / `Puppy` and `mro()`.
- [`code/super_demo.py`](./code/super_demo.py) — calls `super().__init__()` and `super().method()` deliberately, prints what happens.
- [`code/employee_hierarchy.py`](./code/employee_hierarchy.py) — a small `Employee` → `Manager` / `Engineer` example with overridden methods.

## Key terms

base class · derived class · override · `super()` · MRO · `isinstance` · `issubclass` · is-a vs. has-a

**Next →** [Module 05: Polymorphism](../05-polymorphism/)

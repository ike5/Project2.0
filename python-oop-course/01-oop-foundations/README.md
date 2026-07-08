# Module 01 — OOP Foundations

**Goal:** Explain what OOP buys you in plain English, name the four pillars, and recognize that *almost everything* in Python is already an object. ⏱️ ~1.5 h · 🎯 Prereq: 00.

---

## 1. Why OOP, in one sentence

Object-oriented programming is a way to **bundle state and behavior together** so a program reads more like a network of cooperating things than a soup of functions and dicts.

You can write useful Python for years without ever writing a class. So why bother?

- **Namespacing.** A class is a clean box for related data and the functions that operate on it. `dog.bark()` and `cat.meow()` can't accidentally trample each other.
- **Modeling.** Some problems really are about *things*: bank accounts, players, requests, file handles, characters in a game. OOP gives you vocabulary to talk about them.
- **Reuse via inheritance and composition.** Once you've nailed down what a `Shape` does, every new shape is small.
- **Tests get easier.** A class with a clear interface is easy to test in isolation.

The catch: OOP is a tool, not a religion. A two-function script doesn't need a class, and forcing OOP onto a problem it doesn't fit makes code worse. We teach you to recognize when it's the right hammer.

## 2. The four pillars (and what they actually mean in Python)

Most OOP introductions list four pillars. Here's what each one means and how Python *actually* does it — Python skips some pillars' "rules" that languages like Java or C# enforce.

1. **Encapsulation** — keep data and the code that touches it in one place, and *control* how the outside world gets at that data. Python's flavor: by convention (`_name`, `__mangled`) plus the `@property` decorator. No `private` keyword.
2. **Abstraction** — hide the messy internals behind a clean interface. Python's flavor: just write good methods; ABCs and `Protocol` are optional tools, not required.
3. **Inheritance** — define new classes that reuse and extend existing ones. Python's flavor: full support, including multiple inheritance, with a deterministic MRO.
4. **Polymorphism** — the same code works on objects of different types, as long as they support the right interface. Python's flavor: duck typing is the default. ABCs and `Protocol` make it explicit when you want.

We'll spend a whole module on each.

## 3. "Everything is an object" — and why that matters

In Python, *almost everything* you touch is an object with a type, attributes, and methods. Run this in a REPL:

```python
>>> x = 42
>>> type(x)
<class 'int'>
>>> x.bit_length()
6

>>> "hello".upper()
'HELLO'

>>> import math
>>> math.sqrt
<built-in function sqrt>
>>> type(math.sqrt)
<class 'builtin_function_or_method'>
```

A few consequences:

- You can attach attributes to many objects.
- You can pass functions around, store them in lists, return them from other functions.
- The "is it a class or a function?" line is fuzzy — a function *is* an object, and you can write classes whose instances are *callable* (we'll see this with `__call__`).

> **Note:** a few things in Python are *not* regular objects, like keywords (`if`, `def`) and simple statements. Don't sweat it; this is background, not something to memorize.

## 4. Procedural vs. object-oriented, side by side

Here's a tiny program written two ways. Both work. The OOP version groups the data and the function that uses it.

```python
# Procedural
def make_dog(name, age):
    return {"name": name, "age": age}

def dog_bark(d):
    return f"{d['name']}: woof!"

rex = make_dog("Rex", 4)
print(dog_bark(rex))
```

```python
# Object-oriented
class Dog:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def bark(self):
        return f"{self.name}: woof!"

rex = Dog("Rex", 4)
print(rex.bark())
```

The procedural version uses a dict. The OOP version uses a class. The lines are about the same length. The OOP version wins when:

- You have many operations on the same data (`bark`, `fetch`, `eat`, `sleep`).
- You need more than one dog, and the operations need to be the same across them.
- You want to add a class of related things (`Cat`, `Parrot`) and share code.

## 5. Mental model: classes are blueprints

A class is a *blueprint*. Instances are *houses built from the blueprint*. Two houses from the same blueprint are different objects (one is at 1 Main St, the other at 2 Main St), but they share the same floor plan.

```python
class Dog: ...
rex = Dog()
buddy = Dog()
rex is buddy          # False — two different objects
type(rex) is type(buddy)   # True — same class
```

This is the simplest distinction to keep clear: the **class** is the type; the **instance** is the data.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code

- [`code/explore_objects.py`](./code/explore_objects.py) — uses `type()`, `dir()`, and attribute access on real Python objects to convince you everything is an object.
- [`code/dog_procedural_vs_oop.py`](./code/dog_procedural_vs_oop.py) — runs both versions above and prints the same output.

## Key terms

object · class · instance · attribute · method · the four pillars · duck typing · blueprint

**Next →** [Module 02: Classes & Objects](../02-classes-and-objects/)

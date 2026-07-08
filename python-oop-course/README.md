# Python Object-Oriented Programming: From Scripts to Systems 🐍🧱

A hands-on, code-first course that teaches Python by building real object-oriented programs — from your first class to a complete domain model with tests, design patterns, and a capstone.

> **Who this is for.** You already write small Python scripts (functions, lists, dicts, basic modules) and want to level up to designing programs as collections of cooperating objects. By the end you'll read, write, and refactor medium-sized OOP systems confidently — and know when *not* to use a class.

---

## Why this course

Most Python OOP tutorials teach the four pillars in the abstract and then leave you staring at a `Car` / `Boat` / `Vehicle` diagram wondering how any of it maps to your real code. This course is different:

- We teach OOP **as a way to organize Python programs you actually want to write** — text adventures, bank accounts, card games, a domain model for a small library system, a real CLI app.
- Every concept lands in a runnable script. No half-finished snippets.
- We pair the classic vocabulary (encapsulation, inheritance, polymorphism, composition) with **Python's actual idioms** — properties, dataclasses, protocols, duck typing, descriptors, the `abc` module, `__init_subclass__`, and more.

```
                  ┌─────────────────────┐
                  │  procedural Python  │
                  │  (functions, lists)  │
                  └──────────┬──────────┘
                             │
                             ▼
        ┌────────────────────────────────────┐
        │  objects that hold state + methods │
        │        (01, 02, 03)                │
        └────────────────┬───────────────────┘
                         │
            ┌────────────┴────────────┐
            ▼                         ▼
   ┌─────────────────┐       ┌─────────────────┐
   │   inheritance   │       │   composition    │
   │  (04, 05)       │       │   (06)           │
   └────────┬────────┘       └────────┬────────┘
            │                         │
            └────────────┬────────────┘
                         ▼
            ┌────────────────────────┐
            │   magic methods,        │
            │   iteration, operators  │
            │   (07)                  │
            └────────────┬───────────┘
                         ▼
            ┌────────────────────────┐
            │   descriptors, slots,   │
            │   dataclasses, ABCs     │
            │   (08)                  │
            └────────────┬───────────┘
                         ▼
            ┌────────────────────────┐
            │  design patterns +      │
            │  testing OOP code       │
            │  (09, 10)               │
            └────────────┬───────────┘
                         ▼
            ┌────────────────────────┐
            │   CAPSTONE:             │
            │   a real OOP system     │
            │   end-to-end (11)       │
            └────────────────────────┘
```

---

## What makes it effective

- **Learn by doing.** Every module = concepts + a guided lab with expected output + an unguided challenge + reference solutions. The same rhythm as the rest of this repo.
- **Real Python, not pseudo-code.** All examples use modern Python (3.10+) — type hints, dataclasses, match statements, protocols — and follow PEP 8.
- **Idiomatic on purpose.** We don't just show *how* to write a class; we show *why* Python's flavor of OOP looks the way it does, and when to ignore OOP altogether.
- **Tests included.** Module 10 teaches you how to test object-oriented code with `pytest` — including mocking and fixtures. The capstone ships with a test suite.

---

## Prerequisites

- Comfortable with the basics of Python: variables, `if` / `for` / `while`, functions, lists, dicts, importing modules.
- Python 3.10 or newer on your machine. (Some exercises use `match` statements and `|` union types.)
- A terminal and a text editor.
- Curiosity and patience. We'll move from `class Dog: pass` all the way to a multi-module system with tests.

> Need a refresher on the language basics? The [official Python tutorial](https://docs.python.org/3/tutorial/) covers the assumed material in chapters 1–9.

---

## The learning path

| #  | Module | You'll learn to… | Est. |
|----|--------|------------------|------|
| 00 | [Setup & Orientation](./00-setup/) | Install Python, set up a venv, run a script, run a test | 30 min |
| 01 | [OOP Foundations](./01-oop-foundations/) | Explain what OOP buys you, name the four pillars, recognize objects everywhere | 1.5 h |
| 02 | [Classes & Objects](./02-classes-and-objects/) | Define classes with `__init__` and `self`, distinguish instance vs class attributes, write methods | 2 h |
| 03 | [Encapsulation](./03-encapsulation/) | Use `_private` and `__mangled` conventions, write `@property` getters/setters, build read-only state | 1.5 h |
| 04 | [Inheritance](./04-inheritance/) | Inherit from a base class, override methods, call `super()`, read the MRO | 2 h |
| 05 | [Polymorphism](./05-polymorphism/) | Rely on duck typing, define abstract base classes, use `Protocol` for structural typing | 2 h |
| 06 | [Composition](./06-composition/) | Choose "has-a" over "is-a", delegate, model with `@dataclass` | 1.5 h |
| 07 | [Magic Methods](./07-magic-methods/) | Implement `__repr__`/`__str__`/`__eq__`, overload operators, build context managers and iterators | 2 h |
| 08 | [Advanced OOP](./08-advanced-oop/) | Use `__slots__`, descriptors, classmethods/staticmethods, and a peek at metaclasses | 2 h |
| 09 | [Design Patterns](./09-design-patterns/) | Apply Strategy, Observer, Decorator, Factory, and Adapter in idiomatic Python | 3 h |
| 10 | [Testing OOP](./10-testing-oop/) | Test classes with `pytest`, use fixtures, mock collaborators, measure coverage | 2 h |
| 11 | [Capstone](./11-capstone/) | Build a small library management system end-to-end, with tests and a CLI | 3 h |

**Total: ~23 hours of focused work.**

---

## How each module is structured

```
NN-topic/
├── README.md      ← Concepts in plain language. Read this first.
├── lab.md         ← Step-by-step guided lab with expected output. Do this second.
├── code/          ← Reference / starter code the lab uses (where applicable).
├── challenge.md   ← An unguided task to prove you understood it. Do this third.
└── solutions/     ← Reference answers — peek only after you've tried.
```

**The rhythm for every module:** read `README.md` → follow `lab.md` hands-on → attempt `challenge.md` solo → check `solutions/`.

---

## Reference material (keep open)

- **[cheatsheets/python-oop.md](./cheatsheets/python-oop.md)** — One-page syntax reference for class bodies, dunder methods, properties, ABCs, and patterns.
- **[GLOSSARY.md](./GLOSSARY.md)** — Plain-English definitions of every term used in the course.
- **[VERIFY.md](./VERIFY.md)** — Run the smoke tests before Module 00.

---

## Quick start

```bash
cd python-oop-course
python3 -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cat README.md                      # ← you are here
cat VERIFY.md                      # ← run these checks
cd 00-setup && cat README.md       # ← start the course
```

Ready? **→ [Start with Module 00: Setup & Orientation](./00-setup/)**

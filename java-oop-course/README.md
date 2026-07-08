# Java: Object-Oriented Programming — From Fundamentals to Modern Java ☕🧱

A hands-on, local-first course that takes an **experienced programmer who's new to
Java** to a confident, idiomatic **modern Java 21** practitioner who can design
clean object-oriented systems, leverage the type system for safety, and ship
real, testable, multi-module applications.

> **Who this is for:** You already know how to program in *some* language. You
> want to write **idiomatic, modern Java** — not Java 8-era boilerplate. You
> care about the *why* behind OOP choices: when to extend vs. compose, when to
> use a record vs. a class, when generics earn their keep, and how the JVM
> actually behaves at runtime.

> **What's in scope:** the language, the type system, the collections framework,
> the concurrency model, the module system, and the design patterns you'll
> reach for daily. **What's out of scope:** Spring, Jakarta EE, JPA, Android,
> GUI toolkits. The capstone builds a non-GUI application you'll actually
> understand end-to-end.

---

## Why this course is shaped this way

Most "Learn Java" tutorials teach you the language as it was in 2014, then
leave you to discover records, sealed classes, pattern matching, the module
system, and modern concurrency on the job. This course **starts with the
essentials, then goes deep on the modern idioms** — so you write Java that
senior reviewers will recognise in 2026.

```
                ┌───────────────────────────────┐
                │  Phase 0: Java language core   │  ← the foundation
                │  (fast-tracked for you)        │
                └───────────────┬───────────────┘
                                │
        ┌───────────────────────┼────────────────────────┐
        ▼                       ▼                        ▼
 ┌───────────────┐      ┌────────────────┐       ┌──────────────────┐
 │ Phase 1: OOP   │      │ Phase 2: Data & │       │ Phase 3: Modern  │
 │ fundamentals   │      │ functional     │       │ runtime & design │
 │ classes,       │      │ generics,      │       │ concurrency, IO, │
 │ inheritance,   │      │ collections,   │       │ modules,         │
 │ interfaces     │      │ streams        │       │ patterns         │
 └───────────────┘      └────────────────┘       └──────────────────┘
                                │
                                ▼
                   ┌─────────────────────────────┐
                   │  Phase 4: Capstone           │
                   │  Library Management System   │
                   └─────────────────────────────┘
```

**OOP is the trunk; the rest are branches that make the trunk useful.** We nail
encapsulation, polymorphism, and type parameters first, then explore the
collections and functional APIs that turn OOP principles into terse, safe code,
and finally look at the runtime, packaging, and design patterns that make
real systems maintainable.

---

## What makes it effective

- **Learn by doing.** Every module = short concepts + a guided lab (real
  `javac`/`java` projects) + an unguided challenge + reference solutions.
- **Modern Java first.** The course uses **Java 21 (LTS)** throughout: records,
  sealed classes, pattern matching for `instanceof` and `switch`, the enhanced
  pseudo-random number generator, and JPMS. No `Vector`, no
  `new Date().toString()`, no anonymous-class-only callbacks.
- **The full OOP story.** We don't stop at "inheritance and polymorphism." You
  will learn when to *prefer composition*, when *sealed hierarchies* model
  domains better than open inheritance, when *records* replace data classes,
  and how *generics* make collections type-safe.
- **Two capstones.** A guided **design-patterns tour** (Module 14) and a
  substantial **Library Management System** (Module 15) that ties every
  previous module together into a layered, tested, modular application.

---

## Prerequisites

- A Mac or Linux machine with ~5 GB free.
- Experience programming in **any** language. You should be comfortable with
  variables, loops, functions, and at least an intuitive idea of classes.
- Comfort in a terminal. We use the **JDK + `javac`/`java`/`jlink`/`jpackage`**
  plus **VS Code** (or **IntelliJ IDEA Community**).
- **No prior Java knowledge needed.** Module 01 is a focused Java fast-track
  that gets you productive in the language features the rest of the course uses.

Versions used throughout: **Java 21 (LTS)**, **JUnit 5**, **Gradle 8** (build
tool — `javac` is used directly for clarity in early modules).

---

## The learning path

Work the modules **in order** — each builds on the last.

### Phase 0 — Foundations (the language)
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 00 | [Setup & Orientation](./00-setup/) | Install JDK 21, an editor, build your first `Hello.java` | 45 min |
| 01 | [Java Fast-Track](./01-java-fast-track/) | Types, arrays, strings, control flow, `Optional`-free basics | 2 h |

### Phase 1 — OOP fundamentals
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 02 | [OOP Foundations](./02-oop-foundations/) | Classes, encapsulation, immutability, `this`, `static`, packages | 2 h |
| 03 | [Inheritance & Polymorphism](./03-inheritance-polymorphism/) | `extends`, method overriding, `super`, abstract classes, `Object` | 2.5 h |
| 04 | [Interfaces, Records & Sealed Types](./04-interfaces-records-sealed/) | Interfaces (default/static/private methods), `record`, sealed hierarchies, pattern matching | 3 h |

### Phase 2 — The type system & the data layer
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 05 | [Generics & Type Parameters](./05-generics/) | Generic classes/methods, bounded types, wildcards, type erasure, PECS | 3 h |
| 06 | [Collections Deep Dive](./06-collections-deep-dive/) | `List`/`Set`/`Map`/`Queue`/`Deque` — when to use which, complexity, comparators | 2.5 h |
| 07 | [Lambdas, Streams & Functional Interfaces](./07-lambdas-streams/) | Functional interfaces, method references, streams, `Collectors` | 3 h |
| 08 | [Exceptions, `try`-with-resources & `Optional`](./08-exceptions-optional/) | Checked vs. unchecked, custom exceptions, auto-closeable, `Optional` | 2 h |
| 09 | [Enums, Nested & Inner Classes](./09-enums-nested/) | Rich enums, static nested, inner, local, anonymous classes (and when to avoid them) | 2 h |

### Phase 3 — Modern Java, concurrency & design
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 10 | [Annotations, Reflection & Modern Sugar](./10-annotations-reflection-modern/) | Built-in annotations, custom annotations, reflection, `var`, text blocks | 2 h |
| 11 | [Concurrency Essentials](./11-concurrency/) | Threads, `ExecutorService`, `CompletableFuture`, immutability for safety | 3 h |
| 12 | [I/O, NIO.2 & Serialization](./12-io-nio/) | `Path`, `Files`, streams of lines, JSON with Jackson, `Serializable` caveats | 2 h |
| 13 | [Modules (JPMS) & Packaging](./13-modules-jpms/) | `module-info.java`, `requires`/`exports`, `jlink` custom runtimes, JARs | 1.5 h |
| 14 | [Design Patterns in Modern Java](./14-design-patterns/) | Strategy, Decorator, Builder, Factory, Observer, Adapter — and what changed in Java 21 | 3 h |

### Phase 4 — Capstone
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 15 | [Capstone — Library Management System](./15-capstone-library/) | Layered architecture, generics-rich domain, persistence, tests, packaging | 5+ h |

**Total: a realistic ~40 hours of focused, hands-on work.** Go at your own pace.

---

## How each module is structured

```
NN-topic/
├── README.md      ← Concepts in plain language. Read this first.
├── lab.md         ← Step-by-step guided build with expected output. Do this second.
├── code/          ← Starter / reference files the lab adds to your project.
├── challenge.md   ← An unguided task to prove you understood it. Do this third.
└── solutions/     ← Reference answers — peek only after you've tried.
```

**The rhythm for every module:** read `README.md` → follow `lab.md` hands-on →
attempt `challenge.md` solo → check `solutions/`.

---

## The app you build (preview)

The capstone is a **Library Management System** at
[`apps/library/`](./apps/library/) (grown from a single file in Module 02 to a
multi-package, generic-rich, tested, module-aware application by Module 15):

- A domain model of `Book`, `Member`, `Loan` written as **records** where
  appropriate and classes where behaviour matters.
- A **generic repository** abstraction (`Repository<T, ID>`) backed by
  in-memory and JSON-on-disk implementations.
- A **service layer** that enforces business rules with **sealed** result
  types and `Optional` returns.
- A **CLI front-end** that demonstrates `Stream`-driven reports.
- A **JUnit 5 test suite** with at least 80% coverage on the domain.
- A **JPMS module graph** that explicitly `requires`/`exports` the right API.

By the capstone you can:

- Model a domain with the right Java tool (record, sealed class, class with
  invariants).
- Use **bounded generics** and **wildcards** to write reusable algorithms.
- Build **stream pipelines** that read like the problem statement.
- Reason about **thread safety** in terms of immutability and confinement.
- Package and run a **custom JRE** for your application with `jlink`.

---

## Reference material (keep these open)

- **[cheatsheets/java-syntax.md](./cheatsheets/java-syntax.md)** — quick
  reference for an experienced developer.
- **[cheatsheets/oop-cheatsheet.md](./cheatsheets/oop-cheatsheet.md)** — the
  OOP vocabulary, organised.
- **[cheatsheets/collections.md](./cheatsheets/collections.md)** — which
  collection to pick, with complexity and examples.
- **[cheatsheets/streams.md](./cheatsheets/streams.md)** — the stream operators
  worth knowing, with examples.
- **[cheatsheets/jvm-cli.md](./cheatsheets/jvm-cli.md)** — `javac`, `java`,
  `jmod`, `jlink`, `jpackage`.
- **[GLOSSARY.md](./GLOSSARY.md)** — every term defined in plain English.
- **[VERIFY.md](./VERIFY.md)** — end-to-end smoke test of your setup.

---

## Quick start

```bash
# 1. Install the toolchain (Module 00 explains each tool)
cd java-oop-course/00-setup
cat README.md

# 2. Confirm Java works
./scripts/verify-setup.sh

# 3. Start learning
cd ../01-java-fast-track && cat README.md
```

---

Ready? **→ [Start with Module 00: Setup & Orientation](./00-setup/)**

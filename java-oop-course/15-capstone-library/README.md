# Module 15 — Capstone: Library Management System

**Goal:** put everything together. Build a real, layered, **modular**
Java 21 application — a Library Management System — that exercises
every major topic from Modules 02–14.

⏱️ ~5+ h · 🎯 Prereqs: Modules 02–14.

---

## What you're building

A small library system that:

- Tracks **books**, **members**, and **loans** in a generic,
  in-memory repository (with a JSON-on-disk implementation).
- Enforces business rules: a book can't be loaned if it's already
  checked out; a member can hold at most 3 active loans; loans have
  a due date and accrue a fine when overdue.
- Returns **sealed `Result` types** instead of throwing checked
  exceptions for business failures.
- Supports a small **CLI** (text I/O) for adding members, adding
  books, checking out, returning, and listing.
- Ships as a **modular JAR** with a `module-info.java`.
- Has a **JUnit 5 test suite** for the domain and service layers.

## Architecture

```
com.example.library
├── model/        # records and sealed types — the domain
├── service/      # business logic; depends on model + Repository<T,ID>
├── io/           # JSON persistence; depends on model
├── util/         # Result<T,E>, validation helpers
└── Main.java     # CLI; depends on service + io
```

Layering rules:
- `model` depends on nothing in the project.
- `service` depends on `model`.
- `io` depends on `model`.
- `Main` (and tests) depend on `service` and `io`.

This is enforced by the module system: each package is `exports`ed
explicitly.

## The domain (model package)

```java
public record Book(String isbn, String title, String author) {}
public record Member(long id, String name, String email) {}
public record Loan(long id, Book book, Member member, LocalDate borrowedOn, LocalDate dueOn) {}
```

### The `Result<T, E>` sealed type

```java
public sealed interface Result<T, E> permits Result.Ok, Result.Err {
    record Ok<T, E>(T value)  implements Result<T, E> {}
    record Err<T, E>(E error) implements Result<T, E> {}

    static <T, E> Result<T, E> ok(T value) { return new Ok<>(value); }
    static <T, E> Result<T, E> err(E error) { return new Err<>(error); }

    default boolean isOk() { return this instanceof Ok; }
    default T orElseThrow() { /* ... */ }
}
```

Errors are strings (or a sealed `LibraryError` hierarchy; the simpler
version uses strings).

## The repository (a generic interface)

```java
public interface Repository<T, ID> {
    Optional<T> findById(ID id);
    List<T> findAll();
    Result<T, String> save(T value);
    boolean deleteById(ID id);
}
```

Implementations:
- `InMemoryRepository<T, ID>` — backed by a `HashMap`.
- `JsonRepository<T, ID>` — backed by a file (one JSON array).

## The service (service package)

```java
public final class Library {
    private final Repository<Book, String>   books;
    private final Repository<Member, Long>  members;
    private final Repository<Loan, Long>    loans;
    private final Clock clock;
    private final int maxLoansPerMember;

    public Result<Loan, String> checkout(String isbn, long memberId) { /* ... */ }
    public Result<Loan, String> returnBook(long loanId)             { /* ... */ }
    public Result<Member, String> addMember(String name, String email) { /* ... */ }
    public Result<Book, String> addBook(String isbn, String title, String author) { /* ... */ }

    public List<Loan> overdueLoans() { /* ... */ }
    public long fineFor(Loan loan)   { /* ... */ }
}
```

The `Clock` is injected — it lets tests use a fixed clock and real
code use the system clock. (This is the **dependency inversion**
principle from SOLID: depend on an abstraction.)

## The CLI (Main)

A simple `main` that reads commands from `System.in` and writes
results to `System.out`:

```
> add book 1234 "Programming in Java" "Deitel"
> add member 1 "Ada" "ada@example.com"
> checkout 1234 1
> return 1
> list books
> list loans
> quit
```

Each command is parsed and dispatched; results are printed as
`OK: ...` or `ERROR: ...`.

## What you have to build

A runnable, modular, tested application. The reference solution lives
in `solutions/`; build it there if you want to see the working
version, or work through the lab.md for the step-by-step.

---

## Do the lab

Build the Library Management System in stages. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

layered architecture · domain model · sealed `Result<T, E>` · generic
`Repository<T, ID>` · service layer · dependency injection by hand ·
`Clock` for testability · modular JAR · JPMS `exports` for layered
visibility · `jlink` custom JRE

**Next →** [Capstone complete — back to the README](../README.md)

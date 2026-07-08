# Module 11 — Capstone: a small library management system

**Goal:** Bring everything together to build a small but real OOP system end-to-end — a library that holds `Book`s, registers `Member`s, and tracks `Loan`s, with a CLI, a test suite, and a clean separation of concerns. ⏱️ ~3 h · 🎯 Prereq: 10.

---

## 1. The domain

You're going to build a library management system with these concepts:

- **`Book`** — a title, an author, an ISBN, and a `copies` count.
- **`Member`** — a name, an ID, and a list of currently loaned books.
- **`Loan`** — a record that a `Member` borrowed a `Book` on a date, due back on a date.
- **`Library`** — the container: a collection of `Book`s, a collection of `Member`s, a list of `Loan`s. Knows how to lend, return, and look up.

The "borrow a book" workflow:

1. Member asks to borrow a book.
2. Library checks there's a copy available (i.e. copies currently on shelf > 0).
3. If yes, library creates a `Loan` (member + book + dates), decrements available copies, and adds the loan to the member.
4. If no, library raises an error.

The "return a book" workflow:

1. Member returns a book.
2. Library looks up the open loan, marks it returned, and increments available copies.

## 2. The shape of the system

```
python-oop-course/11-capstone/
├── README.md
├── lab.md
├── code/
│   ├── library/
│   │   ├── __init__.py
│   │   ├── book.py
│   │   ├── member.py
│   │   ├── loan.py
│   │   └── library.py
│   ├── cli.py                       ← runnable CLI
│   └── tests/
│       ├── test_book.py
│       ├── test_member.py
│       ├── test_loan.py
│       └── test_library.py
├── challenge.md
└── solutions/
    └── walkthrough.md
```

The `library/` package is the **domain**. The `cli.py` is the **delivery** layer (a thin script that uses the domain). The `tests/` is the **verification** layer.

The design uses:

- **Composition** — a `Library` *has* `Book`s and `Member`s.
- **Encapsulation** — `Book.available` and `Member.active_loans` are properties; `Library._books` is "protected" by convention.
- **Polymorphism / duck typing** — the CLI doesn't care if a "book" is a `Book` or any object with `.title` and `.available`; in practice we use a real `Book`.
- **Dunder methods** — `__repr__` and `__str__` everywhere so logs and the CLI are readable.
- **Dataclasses** — `Loan` is a frozen dataclass; `Book` and `Member` are regular classes with validation.
- **Errors as exceptions** — `LibraryError` is the base; `BookNotFound`, `MemberNotFound`, `NoCopiesAvailable` are specific.

## 3. What "done" looks like

By the end of the module, you should be able to:

```bash
python 11-capstone/code/cli.py list
# Lists all books in the library.

python 11-capstone/code/cli.py borrow --member m1 --isbn 978-0-13-235088-4
# Member m1 borrows Clean Code.

python 11-capstone/code/cli.py return --member m1 --isbn 978-0-13-235088-4
# Member m1 returns Clean Code.

pytest 11-capstone/code/tests/ -v
# All tests pass.
```

The full reference implementation lives in `code/library/` — read it, then make the CLI and the tests your own. The challenge asks you to extend the system in small ways.

## 4. A 60-second tour of the design

- `Book` holds state (title, author, isbn, total copies, available copies) and exposes a read-only `available` property.
- `Member` holds a list of `Loan`s and exposes `active_loans` (a property that filters by `returned_at is None`).
- `Loan` is a frozen dataclass with a `returned_at` field that's `None` until the loan is closed. We don't actually mutate it — we *replace* it with a new `Loan` (frozen makes that the safe pattern).
- `Library` is the orchestrator. It exposes `add_book`, `add_member`, `find_book(isbn)`, `find_member(id)`, `borrow(member_id, isbn)`, `return_book(member_id, isbn)`. It raises domain errors instead of returning `None` or `False`.

> **Note:** the `Loan` pattern is "replace, don't mutate" because the dataclass is frozen. Module 07's `__eq__` / `__hash__` make this safe; you can put `Loan`s in sets and use them as dict keys.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code

- [`code/library/book.py`](./code/library/book.py) — `Book` class
- [`code/library/member.py`](./code/library/member.py) — `Member` class
- [`code/library/loan.py`](./code/library/loan.py) — `Loan` dataclass
- [`code/library/library.py`](./code/library/library.py) — `Library` orchestrator
- [`code/library/errors.py`](./code/library/errors.py) — domain exceptions
- [`code/cli.py`](./code/cli.py) — runnable CLI
- [`code/tests/`](./code/tests/) — the test suite

## Key terms

domain model · composition over inheritance · replace-don't-mutate · domain errors · CLI · `pytest`

🎓 **Congratulations — you have built a complete, tested OOP system.**

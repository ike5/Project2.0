# Lab 11 — Capstone: the library system

**You'll:** run the reference implementation's CLI and test suite, then read the code to internalize the design. ⏱️ ~45 min.
Run from the `python-oop-course/` folder with your venv active.

---

## Part A — Run the test suite

```bash
cd 11-capstone/code
pytest tests/ -v
```

✅ You should see a long list of passing tests across `test_book.py`, `test_member.py`, `test_loan.py`, and `test_library.py`.

## Part B — Run the CLI

```bash
cd 11-capstone/code
python cli.py list
```

✅ You should see the three seeded books.

```bash
python cli.py members
python cli.py borrow --member m1 --isbn 978-0-13-235088-4
python cli.py list
python cli.py return --member m1 --isbn 978-0-13-235088-4
```

✅ `borrow` should print a `Loan(...)` line, `list` should show one fewer copy of Clean Code, and `return` should close the loan.

## Part C — Trigger a domain error

```bash
python cli.py borrow --member m1 --isbn 978-0-201-61622-4
python cli.py borrow --member m1 --isbn 978-0-201-61622-4   # already loaned
```

✅ The second `borrow` should exit non-zero with an error from the library, not a stack trace.

## Part D — Read the code

Open each of the four `code/library/*.py` files in your editor. Read them. The key things to notice:

- `Book` exposes a read-only `available` property; you can't tamper with copies from outside.
- `Loan` is a frozen dataclass — return-don't-mutate in `Library.return_book`.
- `Library` raises specific domain errors; the CLI catches `LibraryError` (the base).
- `Member._add_loan` and `Member._replace_loan` are the only ways the loan list changes — `_loans` stays private.

## Part E — Run with coverage

```bash
cd 11-capstone/code
pytest tests/ --cov=library --cov-report=term-missing
```

✅ Look for any "missing" lines — those are the design decisions you might want to add tests for, or leave as deliberate gaps.

## Cleanup

Nothing to clean up.

## What you learned

- A small, real OOP system: `Book`, `Member`, `Loan`, `Library`, with a CLI and a test suite.
- Composition: the Library *has* books and members; the Loan connects them.
- Replace-don't-mutate: the frozen `Loan` is replaced when returned, not edited.
- Domain errors as exceptions: the CLI catches the base, the rest of the code raises specifics.
- A separation of concerns: domain (`library/`) + delivery (`cli.py`) + verification (`tests/`).

➡️ **[challenge.md](./challenge.md)** then [walkthrough.md](./solutions/walkthrough.md) for the design notes.

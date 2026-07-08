# Capstone — Reference Walkthrough

Notes on the design of the library system. This is the *why* of `code/library/`. Read it after running the lab and trying the challenge.

## 1. The shape of the system

```
┌─────────────┐
│  Book       │   value-like; once added, mostly read
└─────┬───────┘
      │ has many
      ▼
┌─────────────┐
│  Library    │   orchestrator
└─────┬───────┘
      │ has many
      ▼
┌─────────────┐
│  Member     │   has a list of Loans
└─────┬───────┘
      │ owns
      ▼
┌─────────────┐
│  Loan       │   frozen dataclass, replace-don't-mutate
└─────────────┘
```

The four concepts you find in a library catalog. The relationships:

- A `Library` has many `Book`s and many `Member`s.
- A `Loan` connects a `Member` to a `Book` for a window of time.
- A `Book` knows how many copies are *currently available*; it doesn't know about `Member`s.
- A `Member` knows its own loans; it doesn't know about other members or the Library's storage.

That's deliberate. `Book` and `Member` are useful on their own — you can construct a `Book` and print it, you can construct a `Member` and list its loans, all without a `Library`. The `Library` ties them together with workflows.

## 2. Why `Loan` is a frozen dataclass

A `Loan` has no behavior worth varying. It's a record: who, what, when borrowed, when due, when returned. Frozen + `__eq__` + `__hash__` means:

- It can be a dict key or a set element.
- It can't be silently mutated.
- Equality is value-based (`Loan("m1", "1", ...) == Loan("m1", "1", ...)`).

When the member returns the book, the `Library` builds a *new* `Loan` with `returned_on` set, and uses `Member._replace_loan` to swap it in. The original loan is referenced by index — its dataclass-ness is what makes the swap work cleanly.

This is the same pattern as immutable state in functional programming, but expressed in plain Python.

## 3. Why `Book._take_one` is private

`Book._take_one` and `Book._return_one` start with an underscore and live alongside public properties. They're called *only* by `Library` during a borrow/return. They enforce the invariant: `0 <= available <= total`. If random code could call them, you could put the library into a state where `available` is negative or greater than `total`.

This is the encapsulation pattern from Module 03, used deliberately: the *primitive* (`Book`) is dumb about policy; the *orchestrator* (`Library`) is the only thing that runs the policy.

## 4. Why domain errors are a hierarchy

```python
LibraryError       # catch-all for "anything went wrong in the library"
├── BookNotFound
├── MemberNotFound
├── NoCopiesAvailable
├── LoanNotFound
└── AlreadyReturned
```

The CLI catches `LibraryError` to convert *any* library problem into a clean error message and a non-zero exit code. Inside the library, code raises the *most specific* error. A test can check for `pytest.raises(NoCopiesAvailable)` to be precise; the CLI doesn't have to.

If you find yourself wanting to add `LoanLimitReached` for the challenge, that's the pattern: subclass `LibraryError` and the CLI gets the right behavior for free.

## 5. Why a CLI, and why a thin one

The CLI is *one* delivery layer for the system. Tomorrow you might add a web layer, or a Discord bot. None of those should know about `Book._take_one`. They should call `library.borrow(member_id, isbn)`. That's the whole point of the orchestrator.

`cli.py` is short on purpose: argparse for the subcommands, a `seed_library()` helper, a dispatch table, and a `try/except LibraryError` at the top. If a future you wants to add `--json` output, only `cli.py` changes.

## 6. Where the patterns from Module 09 show up

You can read the patterns in the design:

- **Encapsulation** — `Book._available` is a private field with a read-only `available` property.
- **Composition** — `Library` *has* books and members; `Member` *has* loans.
- **Replace-don't-mutate** — `Loan` is frozen, returned-loan state is a new `Loan`.
- **Polymorphism / duck typing** — the CLI prints `Book.__str__` and `Member.__str__`; if you add a `Magazine` class with a `__str__`, the CLI doesn't need to change.
- **Domain errors** — the `LibraryError` hierarchy, used consistently.
- **Factory** — the CLI's `seed_library()` is a tiny factory: it builds a fresh in-memory `Library` for each run.
- **Adapter** — implicit in the CLI: it adapts argparse's arguments into a `Library.borrow(member_id, isbn)` call.

You don't need to name a pattern every time you use it. But once you know the names, you can talk about the design in one sentence: "A `Library` orchestrator with immutable `Loan`s, exception-based errors, and a thin CLI delivery layer." That sentence *is* the design.

## 7. Tests as a design check

The test suite is a *second* description of the system. Read `test_library.py` and you can tell what's important:

- `test_borrow_creates_loan_and_decrements_available` — borrowing decreases availability.
- `test_borrow_last_copy_then_blocked` — borrowing the last copy works, the next one fails.
- `test_return_reopens_availability` — return is the inverse of borrow.
- `test_borrow_then_return_then_borrow_again` — the system is reusable.

If a future change breaks one of these, you have an exact pointer to the broken invariant. The test names *are* the requirements.

## 8. How to extend (the recipe)

When you add a feature — say, reservations, fines, or different book types — the recipe is:

1. Decide which class owns the new state (probably `Library` for policy, `Book`/`Member` for facts).
2. Add a method to that class with a clear name and a clear error.
3. Write the test *first* if you can — at least write the test before you move on.
4. Add a CLI subcommand only if a human will use it.
5. Run the suite. If anything breaks, fix it before adding more.

The whole library system is a few hundred lines. The patterns that make it small and readable — composition, replace-don't-mutate, domain errors, separation of concerns — are the same patterns that scale to thousands of lines. That's the lesson.

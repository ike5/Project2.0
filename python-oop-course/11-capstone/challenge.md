# Challenge 11 — Capstone

Solutions in [`solutions/walkthrough.md`](./solutions/walkthrough.md). Try first.

This module's "challenge" is bigger than the others. The reference implementation in `code/library/` is the cleanest possible starting point. Your job is to *extend* it in three small ways, write tests for each, and prove the CLI still works.

## Tasks

1. **Add a `due_on` to the CLI.** Extend `cli.py` so `python cli.py borrowed --member m1` prints each of that member's active loans with its `due_on` date and an "OVERDUE" marker if it's past due. (hint: `Member.active_loans` is already a property; iterate it and use `Loan.is_overdue`.)
2. **Add a "max active loans" rule.** Extend `Member` to track a `max_active_loans: int` (default 5). Add a `Library.borrow` check: if the member already has `>= max_active_loans` active loans, raise a new domain error `LoanLimitReached`. Write a test. (hint: subclass `LibraryError` in `errors.py`.)
3. **Add a `Library.search(query)` method.** It should return books whose title or author contains `query` (case-insensitive). Use it in the CLI: `python cli.py search --query clean`. (hint: `return [b for b in self._books.values() if query.lower() in b.title.lower() or query.lower() in b.author.lower()]`.)
4. **(Stretch) Persist the library to JSON.** Add `Library.save(path)` and `Library.load(path)` methods that round-trip the books, members, and loans to/from a JSON file. (hint: serialize each `Book` as a dict, then `json.dump` a dict with `"books"`, `"members"`, `"loans"` keys. For loans, the `date` fields need a string format like `"2026-01-15"`.)

## Success criteria

- [ ] `python cli.py borrowed --member m1` shows a member's active loans.
- [ ] Borrowing past the limit raises `LoanLimitReached`; the CLI prints a friendly error.
- [ ] `python cli.py search --query clean` finds "Clean Code."
- [ ] (Stretch) `lib.save("lib.json")` and `Library.load("lib.json")` round-trip cleanly.
- [ ] All existing tests still pass.

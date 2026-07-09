# Challenge 15 — Capstone Extensions

Solution in [`solutions/`](./solutions/). Try first.

The capstone is large; the challenge is a set of *extensions* that
exercise the full stack. Each builds on the previous.

## Tasks

1. **JSON repository.** Write `JsonRepository<T, ID>` that persists a
   list of records to a JSON file. Use a tiny hand-rolled JSON encoder
   (no external library) for the record fields, or use reflection. Load
   on construction, save on each `save`/`delete`. (The reference uses a
   simple per-record JSON via a small `toJson`/`fromJson` interface
   the model implements.)

2. **A `BookCopy` concept.** Instead of one book per ISBN, model
   `BookCopy(long id, Book book)` so the same ISBN can have multiple
   physical copies. Update `Library.checkout` to take a copy id, not
   an ISBN.

3. **Author search.** Add `Library.searchByAuthor(String author)` that
   returns all books with a (case-insensitive) substring match on
   author. Add a CLI command `search <author>`.

4. **Statistics.** Add a `LibraryStats` record with `int bookCount`,
   `int memberCount`, `int activeLoans`, `int overdueLoans`,
   `long outstandingFinesCents`. Add a `stats` command to the CLI.

5. **Concurrency.** The `InMemoryRepository` is concurrent-safe (uses
   `ConcurrentHashMap`), but the `Library` is not — two concurrent
   `checkout` calls for the same book could both pass the
   "already loaned" check. Add a `ReentrantLock` (or use
   `compute`/`synchronized` on the relevant state) to make `checkout`
   atomic. Add a test that calls `checkout` from two threads
   simultaneously and confirms only one succeeds.

6. **Modular JAR + `jlink`.** Add a `module-info.java` that exports
   `model`, `util`, and `service`; `Main` lives in the unnamed package
   for now. Build a custom JRE with `jlink` and confirm the CLI runs.

## Success criteria

- [ ] The solution has all six features and a clean compile.
- [ ] Tests for each new feature.
- [ ] The `module-info.java` enforces the layering (e.g. `io` package
      not exported to outside callers).

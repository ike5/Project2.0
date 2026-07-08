# Challenge 08 — Exceptions, `try`-with-resources & `Optional`

Solution in [`solutions/`](./solutions/). Try first.

## Tasks

1. **A `CsvLineReader` that uses `try`-with-resources.** Write
   `List<List<String>> readCsv(Path path)` that opens the file with
   `Files.newBufferedReader`, splits each non-blank line on commas, and
   returns the rows. Use `try`-with-resources. Throw a checked
   `IOException` (no need to wrap).

2. **A checked `ServiceException` with a cause.** Add a method
   `requirePositive` to a `MathService` class that throws
   `ServiceException("must be positive: " + x)` when `x <= 0`. Catch an
   underlying `IllegalArgumentException` and rethrow as the checked
   `ServiceException` with the original as `cause`.

3. **`Optional<T>` everywhere it belongs.** Write
   `Optional<User> findUserByEmail(List<User> users, String email)`. Show
   that the caller can chain `flatMap` to read the user's `Optional<Address>`
   and `.map` to extract a `String` country code.

4. **A custom `AutoCloseable`.** Write a `Timer implements AutoCloseable`
   that records the time when constructed, prints the elapsed
   milliseconds when `close()` is called, and has a main that uses it
   inside `try (...)`. (`Thread.sleep(100)` in the body to make it
   visible.)

5. **An uncaught exception handler.** Write a `Thread.UncaughtExceptionHandler`
   that logs the thread name and the exception. Install it as the default
   for the JVM (`Thread.setDefaultUncaughtExceptionHandler`). Show that
   an uncaught exception in a `main` thread goes through the handler.

## Success criteria

- [ ] `readCsv` uses `try`-with-resources and reads a comma-separated
      file.
- [ ] `requirePositive` rejects non-positive input with a checked
      exception carrying the cause.
- [ ] `findUserByEmail(...).flatMap(User::address).map(Address::country)`
      returns `Optional<String>` (no `.isPresent` then `.get`).
- [ ] `Timer` implements `AutoCloseable` and logs the elapsed time when
      closed.
- [ ] The uncaught-exception handler is invoked when `main` throws.

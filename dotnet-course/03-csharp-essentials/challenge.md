# Challenge 03 — Essentials in Anger

Solution in [`solutions/`](./solutions/). Try first.

## Tasks
1. **LINQ report.** Given a list of `LogEntry(DateTime Time, string Level, string Message)`,
   produce: counts per level (descending), the 3 most recent `Error` messages, and
   whether any `Error` occurred in the last hour. One LINQ pipeline per result.

2. **Generic `Result<T>`.** Implement a `Result<T>` type with `IsSuccess`, `Value`,
   and `Error`, plus static `Ok(value)` / `Fail(error)` factories. Write a
   `Result<int> ParseAge(string s)` that returns `Fail` (not an exception) on bad input.

3. **Exception discipline.** Write `T Retry<T>(Func<T> action, int times)` that retries
   on exception up to `times`, re-throwing the last one if all attempts fail. Use
   `throw;` correctly and don't swallow the final error.

4. **Disposable.** Write a `class Timer : IDisposable` that records a start time and,
   on `Dispose`, prints the elapsed milliseconds. Use it with `using` around some work.

## Success criteria
- [ ] Each LINQ result is a single, readable pipeline.
- [ ] `ParseAge` reports failure via `Result<int>`, never throws on bad input.
- [ ] `Retry` retries the right number of times and preserves the final stack trace.
- [ ] `Timer` prints elapsed time deterministically via `using`.

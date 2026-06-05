# Challenge 04 — Runtime & Async

Solution in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Solution layout.** Create a solution with `Bank.Core` (classlib), `Bank.App`
   (console), and `Bank.Tests` (xunit). Wire references so the app and tests both use
   Core. Confirm `dotnet test` discovers the (empty) test project.

2. **Concurrent fan-out.** Write `async Task<int[]> DownloadAllAsync(string[] urls)`
   that simulates downloads with `Task.Delay` (length derived from the url) and runs
   them **concurrently**, returning all sizes. Prove (with a stopwatch) it's faster
   than doing them sequentially.

3. **Don't block.** Explain in a comment why `var x = SomeAsync().Result;` is
   dangerous, and rewrite a small `Main`-style flow to be `async` end-to-end instead.

4. **Cancellation (stretch).** Add a `CancellationToken` to `DownloadAllAsync` and
   cancel after 100ms; show that in-flight work observes the cancellation.

## Success criteria
- [ ] 3-project solution builds; `dotnet test` runs.
- [ ] Concurrent fan-out is measurably faster than sequential.
- [ ] You can articulate the `.Result` deadlock/starvation risk and avoid it.
- [ ] (Stretch) Cancellation propagates via the token.

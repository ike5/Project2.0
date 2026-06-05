# Challenge 05 — Diagnose & Cover

Solution in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Trace reading.** Given this trace, state (a) the exception type, (b) the most
   likely line of *your* code to inspect, (c) a one-line hypothesis:
   ```
   System.FormatException: The input string 'N/A' was not in a correct format.
      at System.Number.ParseInt32(...)
      at Billing.Importer.ParseRow(String[] cols) in Importer.cs:line 57
      at Billing.Importer.Import(String path) in Importer.cs:line 22
   ```

2. **Theory test.** Write a `[Theory]` for a `Fizzbuzz(int n)` function covering
   3→"Fizz", 5→"Buzz", 15→"FizzBuzz", 7→"7". Implement `Fizzbuzz` to pass.

3. **Exception test.** Write a test asserting that `Inventory.Remove(name)` throws
   `KeyNotFoundException` when the item isn't present, using `Assert.Throws`.

4. **Async test.** Add a test to a copy of TaskApi proving `CreateAsync` followed by
   `GetAllAsync` returns exactly one task with the trimmed title (use EF InMemory).

## Success criteria
- [ ] Correct exception type, suspect line (57), and a sensible hypothesis (a column
      held `'N/A'` and `int.Parse` failed → use `int.TryParse`).
- [ ] `[Theory]` covers all four FizzBuzz cases and passes.
- [ ] Exception test uses `Assert.Throws<KeyNotFoundException>`.
- [ ] Async test uses `ThrowsAsync`/awaited assertions correctly.

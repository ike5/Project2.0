# Challenge 04 — Interfaces, Records & Sealed Types

Solution in [`solutions/`](./solutions/). Try first.

## Tasks

1. **A `Result<T>` sum type.** Build a `sealed interface Result<T>` with
   exactly two permitted records: `Success<T>(T value)` and
   `Failure<T>(String message, Throwable cause)`. Write the static
   factories `Result.ok(T)` and `Result.error(String, Throwable)`. Show in
   a `main` that an exhaustive `switch` on `Result<String>` covers both
   cases.

2. **A `Money` record with custom `toString` and `add`.** Write
   `record Money(long cents, Currency currency)`. The compact constructor
   validates `cents >= 0` and non-null currency. Add `add(Money)` that
   throws on currency mismatch. Override `toString` to print
   `"$12.34 USD"`-style. **Bonus:** override `equals` to also consider
   currency.

3. **A `sealed` `Shape` with mixed kinds.** Build
   `sealed interface Shape permits Circle, Rectangle, Triangle` (extend
   Module 03's hierarchy). Provide a `default String describe()` on the
   interface that uses each implementation's `kind()`. Use a
   pattern-matching `switch` to render them.

4. **Pattern matching for `instanceof` chain.** Without changing the type
   of `Object o`, write a `String describeShape(Object o)` that returns
   the right description for `Circle`, `Rectangle`, `Triangle` (from
   task 3) and `"not a shape"` for everything else — using `instanceof`
   pattern matching with a chain of `if`s.

## Success criteria

- [ ] `Result<T>` is exhaustively matchable; the compiler complains if
      you remove a case from a `switch`.
- [ ] `Money` validates in the compact constructor and refuses
      cross-currency `add`.
- [ ] `Shape` is `sealed`; the `describe()` works polymorphically.
- [ ] `describeShape(Object)` correctly branches with `instanceof` patterns
      and never throws.

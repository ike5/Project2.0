# Challenge 02 — OOP Foundations

Solution in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Immutable `Money` (without records).** Build `Money` as a *class* (not
   a record — this exercise is about doing the immutability work yourself).
   Fields `cents` and `currency`, both `private final`. Validate in the
   constructor. Provide `add(Money)`, `subtract(Money)`, `multiply(int)`,
   and a static factory `usd(long)`. Defensive-copy the `Currency` if you
   need to (you probably don't — `Currency` is immutable).

2. **Encapsulation that bites.** Add a method
   `void applyMonthlyInterest(BigDecimal rate)` to your `BankAccount` (or a
   new `SavingsAccount` class). Demonstrate what happens if the field is
   `public` vs. `private`. The key point: with `public`, an outside caller
   can set the rate to `-1`, and the next month the balance goes *negative*
   in a way your object can't reject. With `private`, the setter (or the
   method) rejects bad input.

3. **`equals`/`hashCode` for a value class.** Build a `Color` class with
   `red`, `green`, `blue` (all `int`, 0..255). Override `equals` and
   `hashCode` based on the three fields. Verify with `Set<Color>` that two
   `Color` instances with the same RGB are treated as the same set member.

4. **Defensive copy.** Write a `Team` class that holds a `List<String>
   members`. Make sure that:
   - The constructor's input is defensively copied.
   - The accessor returns a *view* that throws on mutation (`Collections.unmodifiableList`).
   - Demonstrate that a caller mutating the input list does not affect the
     `Team`'s state, and that mutating the accessor's result throws.

## Success criteria

- [ ] `Money` rejects negative amounts in the constructor and from the
      factory. `Money.add`/`subtract` reject currency mismatch.
- [ ] `applyMonthlyInterest` rejects negative rates; the field is `private`.
- [ ] `Color` correctly equal/hashCodes; `Set<Color>` deduplicates by RGB.
- [ ] `Team` does not let external mutation leak in or out.

# Challenge 14 — Design Patterns

Solution in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Strategy: a `Discount` hierarchy.** Build
   `interface Discount { BigDecimal apply(BigDecimal price); }` and three
   implementations: `NoDiscount`, `PercentageDiscount(rate)`,
   `BulkDiscount(threshold, percent)`. Build a `Cart` that takes a
   `Discount` and applies it to its total.

2. **Decorator: a logging `Repository<T>`.** Build
   `interface Repository<T, ID> { Optional<T> findById(ID id); List<T> findAll(); }`
   and a `LoggingRepository` that wraps another repository and prints
   each operation as it happens.

3. **Builder: a `Money` builder for compound expressions.** Build a
   `MoneyBuilder` that lets you write
   `money().usd(10_00).plus(usd(5_00)).minus(usd(2_00)).build()`.

4. **Factory: a `Shape` factory.** Combine Module 04's `sealed Shape`
   with a `Shape.of(String kind)` factory that returns the right
   record.

5. **Observer: a `Ticker`.** Build a `Ticker` that runs a task every N
   milliseconds, with `subscribe(Consumer<Long>)` (passing the current
   tick) and an unsubscribe handle. Use it to print the current tick
   to stdout for 3 ticks, then unsubscribe.

6. **Singleton: a config holder.** Write
   `public final class AppConfig { ... }` whose `get()` returns a
   single immutable instance, with a public constructor that takes the
   initial values and a `private` constructor for the default. (Hint:
   a `record` with a static field.)

## Success criteria

- [ ] `Discount` strategies compose with `Cart`.
- [ ] `LoggingRepository` logs every call.
- [ ] The `MoneyBuilder` produces a `Money` that has the right total.
- [ ] `Shape.of("circle")` returns a `Circle`; unknown kinds throw.
- [ ] The `Ticker` ticks three times and then stops.
- [ ] `AppConfig.get()` returns the same instance every call.

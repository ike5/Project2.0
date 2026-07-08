# Challenge 07 — Lambdas, Streams & Functional Interfaces

Solution in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Top-N most frequent items.** Given a `List<String> words`, return the
   `n` most-frequent words in descending order of frequency, breaking
   ties alphabetically. Use `Collectors.groupingBy` + a stream pipeline
   (no `for` loops).

2. **A `Function` chain.** Build a `Function<String, String>` that
   trims, lowercases, replaces runs of whitespace with a single space,
   and removes leading/trailing punctuation (`.`, `,`, `!`, `?`).
   Compose it from smaller `Function`s using `.andThen` or
   `.compose`.

3. **A custom `Collector` for median.** Implement a `Collector<Integer,
   ?, OptionalDouble>` that, given a stream of integers, returns the
   median. (Hint: you need both a "finisher" and a "combiner" — or use
   `Collector.of` with a mutable accumulator.) Show that
   `Stream.of(1,2,3,4,5).collect(median())` is `3.0` and
   `Stream.<Integer>of()` is `OptionalDouble.empty()`.

4. **`Optional` chain.** Given `findUser(long)` returning
   `Optional<User>`, `User::primaryAddress` returning `Optional<Address>`,
   and `Address::countryCode` returning `String`, write
   `Optional<String> countryOf(long userId)` that returns the user's
   country code or `Optional.empty()`.

5. **A `Predicate` and a `Supplier`.** Build a method
   `static <T> List<T> takeUntil(List<T> xs, Predicate<T> p)` that
   returns the prefix of `xs` up to (but not including) the first element
   that fails the predicate. (This is the *opposite* of `takeWhile`.)
   Provide a `Supplier` factory `randomInts(int n)` that yields a
   `Stream<Integer>` of `n` random integers, and use it to test
   `takeUntil`.

## Success criteria

- [ ] Top-N works with `Collectors.groupingBy` only.
- [ ] The `Function` chain reads as a clear sequence of transforms.
- [ ] Your median collector handles empty streams.
- [ ] `countryOf` returns the right thing for missing user, missing
      address, etc.
- [ ] `takeUntil` stops at the first failing element and includes
      nothing past it.

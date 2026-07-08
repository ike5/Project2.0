# Challenge 05 — Generics

Solution in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Generic `Result`-aware `Map` operation.** Write
   `<K, V> Result<V> getOr(Map<K, V> map, K key, V fallback)` (or use
   `Map.getOrDefault`) that returns a `Result<V>` — `Success` if the key
   was present, `Failure` with a message if it wasn't. Re-use your
   `Result<T>` from Module 04's challenge (or copy it in).

2. **Bounded `min` and `max` by a `Comparator`.** Write
   `static <T> T min(Collection<T> xs, Comparator<T> cmp)` and the
   `max` you saw in the lab. They should return `Optional<T>` rather
   than throwing on an empty collection.

3. **PECS `merge` method.** Write
   `<K, V> void mergeMaps(Map<K, V> target, Map<? extends K, ? extends V> source)`
   that copies every entry of `source` into `target`. Confirm that
   `Map<String, Integer>` can be merged into a `Map<Object, Object>`.

4. **An `Either<L, R>` sum type as a record.** Write
   `sealed interface Either<L, R> permits Left, Right` with
   `record Left<L,R>(L value)` and `record Right<L,R>(R value)`.
   Write `<L, R> R orElse(Either<L, R> e, R fallback)` that returns
   the `Right` value or the fallback.

5. **Wildcard reachability test.** Try to write
   `void add(List<? extends Number> xs, Integer i) { xs.add(i); }` and
   see why it doesn't compile. Then write a method that *does* add
   integers to a `List<Number>` (no wildcard), and explain in a
   sentence the difference.

## Success criteria

- [ ] `getOr` returns `Result.Success` for a present key and
      `Result.Failure` for a missing key.
- [ ] `min`/`max` return `Optional<T>` and never throw on empty input.
- [ ] `mergeMaps` accepts a `Map` whose value type is a subtype of the
      target's value type.
- [ ] `Either` is exhaustively matchable; `orElse` returns the `Right`
      or the fallback.
- [ ] You can articulate why `List<? extends Number>` is not addable.

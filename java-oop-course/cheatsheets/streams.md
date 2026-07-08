# Streams Cheatsheet

A stream is a **declarative pipeline** over a sequence of values. You don't say
*how*; you say *what*. The runtime decides *how*.

## Lifecycle

```
        source                intermediate ops              terminal op
     ────────────         ─────────────────────          ──────────────
List.of(1,2,3,4,5)  →   .filter(n -> n%2==0)   →     .collect(toList())
                       .map(n -> n*n)                 .sum()
                       .sorted(...)                   .forEach(...)
                       .distinct()
                       .limit(10)
```

Intermediate operations are **lazy** — they don't run until the terminal op
fires. That lets the runtime fuse operations and short-circuit.

## The ten operations worth knowing

### Source / build

```java
list.stream()
collection.parallelStream()                  // uses ForkJoinPool common pool
Stream.of(1, 2, 3)
Stream.<String>empty()
Stream.iterate(0, n -> n + 1).limit(10)      // 0..9
Stream.generate(Math::random).limit(5)        // 5 random doubles
Files.lines(path)                            // Stream<String>
Pattern.compile("\\w+").splitAsStream(s)     // tokeniser stream
```

### Intermediate (return a `Stream<T>`)

```java
.filter(predicate)            // keep elements matching predicate
.map(fn)                      // transform T -> R
.flatMap(fn)                  // transform T -> Stream<R> and flatten
.mapToInt / mapToLong / mapToDouble   // to a primitive stream (faster)
.distinct()                   // stateful, removes duplicates
.sorted()                     // stateful, natural order
.sorted(comparator)           // stateful, custom order
.peek(consumer)               // for debugging; don't mutate
.limit(n)                     // short-circuiting
.skip(n)                      // short-circuiting
.takeWhile(p)                 // Java 9+, short-circuit
.dropWhile(p)                 // Java 9+
```

### Terminal (close the stream)

```java
.collect(Collectors.toList())         // -> List<T>   (use .toList() in Java 16+)
.collect(Collectors.toSet())          // -> Set<T>
.collect(Collectors.toMap(k, v))      // -> Map<K, V>
.collect(Collectors.groupingBy(k))    // -> Map<K, List<T>>
.collect(Collectors.partitioningBy(p))// -> Map<Boolean, List<T>>
.collect(Collectors.joining(", "))    // -> String
.toList() / .toSet() / .toMap(...)    // Java 16+
.count()                              // long
.sum() / .average() / .min() / .max() // on primitive streams only
.findFirst() / .findAny()             // Optional<T>
.anyMatch(p) / .allMatch(p) / .noneMatch(p)   // boolean
.forEach(consumer)                    // side-effecting
.reduce(identity, accumulator)        // fold
```

## Common patterns

### Group / count

```java
Map<String, Long> counts =
    words.stream().collect(Collectors.groupingBy(w -> w, Collectors.counting()));
```

### Partition

```java
Map<Boolean, List<Integer>> evenOdd =
    nums.stream().collect(Collectors.partitioningBy(n -> n % 2 == 0));
```

### Top N

```java
List<String> top3 = items.stream()
        .sorted(Comparator.comparingInt(String::length).reversed())
        .limit(3)
        .toList();
```

### Build a map

```java
Map<String, User> byId = users.stream()
        .collect(Collectors.toMap(User::id, Function.identity()));
```

### Sum a property

```java
int total = orders.stream()
        .mapToInt(Order::totalCents)
        .sum();
```

### Join strings

```java
String csv = rows.stream()
        .map(Row::toCsv)
        .collect(Collectors.joining(",\n"));
```

## Optional and streams

```java
Optional<Order> latest = orders.stream()
        .max(Comparator.comparing(Order::placedAt));
String id = latest.map(Order::id).orElse("(none)");
```

## Don't use streams for…

- Loops with complex state machines (multiple `int` counters, nested
  conditions with side effects). A `for` loop is clearer.
- Anything that throws inside a lambda in a way that needs careful
  handling. Streams amplify checked-exception pain.
- Single-element processing. Just call the function.

## Watch out

- **Streams are single-use.** Once you call a terminal op, the stream is
  gone. Create a new one.
- **`.parallelStream()` is not always faster.** For small data sets or
  expensive spliterators it's slower. The benchmark rule: don't guess.
- **`.forEach` doesn't guarantee order on parallel streams.** Use
  `.forEachOrdered` if order matters.
- **Don't mutate external state from `map`/`filter`.** Streams favour pure
  functions; side effects make debugging painful.
- **`Collectors.toMap` throws on duplicate keys.** Provide a merge
  function: `toMap(k, v, (a, b) -> a)`.

## Bonus: primitive streams

`IntStream`, `LongStream`, `DoubleStream` avoid boxing. Useful methods:

```java
IntStream.range(0, 10)        // 0..9
IntStream.rangeClosed(1, 6)  // 1..6 (inclusive)
IntStream.of(1, 2, 3).sum()   // 6
IntStream.of(1, 2, 3).average()   // OptionalDouble[2.0]
int sum = stream.mapToInt(String::length).sum();
```

`Stream<Integer>` → `IntStream`: `.mapToInt(Integer::intValue)`.
`IntStream` → `Stream<Integer>`: `.boxed()`.

# Module 07 — Lambdas, Streams & Functional Interfaces

**Goal:** write fluent, declarative code with **lambdas**, **method
references**, and the **Streams API**. The work of the last 15 years of
Java lives here.

⏱️ ~3 h · 🎯 Prereq: Module 06.

---

## 1. Functional interfaces

A **functional interface** is an interface with exactly one abstract
method. It's the target type of a lambda.

The most-used ones in `java.util.function`:

| Interface | Signature | What it means |
|-----------|-----------|---------------|
| `Function<T, R>` | `R apply(T)` | transform T to R |
| `Consumer<T>` | `void accept(T)` | side-effect on T |
| `Supplier<T>` | `T get()` | produce a T |
| `Predicate<T>` | `boolean test(T)` | true/false question |
| `UnaryOperator<T>` | `T apply(T)` | T → T (specialised `Function`) |
| `BinaryOperator<T>` | `T apply(T, T)` | T + T → T (specialised `BiFunction`) |
| `BiFunction<T, U, R>` | `R apply(T, U)` | (T, U) → R |

Plus all the `*To*` primitive specialisations:
`IntFunction<R>`, `ToIntFunction<T>`, `ObjIntConsumer<T>`, etc. These
avoid boxing for performance.

You can declare your own — annotate it `@FunctionalInterface` so the
compiler checks that there's exactly one abstract method:

```java
@FunctionalInterface
public interface Transformer<I, O> {
    O transform(I input);
}
```

## 2. Lambdas

A lambda is an anonymous function value. Its syntax:
```java
(parameters) -> expression-or-block
```

```java
Function<String, Integer> length = s -> s.length();
Predicate<String> isBlank    = s -> s.isBlank();
Consumer<String> print       = s -> System.out.println(s);
Supplier<Long> now           = () -> System.currentTimeMillis();
BinaryOperator<Integer> add  = (a, b) -> a + b;
```

**Type inference** usually works; the compiler knows the target type
because the lambda is being assigned to a functional-interface variable
or passed to a method. You rarely write `(String s) ->` — `s ->` is fine.

## 3. Method references

A method reference is a lambda that delegates to an existing method.

```java
// equivalent lambdas
Function<String, Integer> length1 = s -> s.length();
Function<String, Integer> length2 = String::length;        // instance method on parameter

Consumer<String> print1 = s -> System.out.println(s);
Consumer<String> print2 = System.out::println;             // instance method on receiver

Supplier<List<String>> empty1  = () -> new ArrayList<>();
Supplier<List<String>> empty2  = ArrayList::new;            // constructor

Function<String, Integer> parse1 = s -> Integer.parseInt(s);
Function<String, Integer> parse2 = Integer::parseInt;        // static method
```

Four flavours:
- `Type::staticMethod` — `Math::abs`
- `instance::method` — bound to that instance: `System.out::println`
- `Type::instanceMethod` — bound to the first lambda parameter: `String::length`
- `Type::new` — constructor

## 4. The Streams API

A `Stream<T>` is a **lazy, declarative pipeline** of operations on a
sequence of values. The runtime decides *how*; you say *what*.

```
        source                intermediate ops              terminal op
     ────────────         ─────────────────────          ──────────────
List.of(1,2,3,4,5)  →   .filter(n -> n%2==0)   →     .collect(toList())
                       .map(n -> n*n)                 .sum()
                       .sorted(...)                   .forEach(...)
                       .distinct()
                       .limit(10)
```

Intermediate operations are **lazy** — they don't run until a terminal
operation fires. The runtime can then fuse operations and short-circuit.

```java
List<String> result = List.of("Ada", "Grace", "Alan", "Bob")
    .stream()
    .filter(s -> s.length() > 3)
    .map(String::toUpperCase)
    .sorted()
    .toList();   // Java 16+
```

### Source / build

```java
list.stream()
collection.parallelStream()                  // uses ForkJoinPool
Stream.of(1, 2, 3)
Stream.<String>empty()
Stream.iterate(0, n -> n + 1).limit(10)      // 0..9
Stream.generate(Math::random).limit(5)        // 5 random doubles
Files.lines(path)                            // Stream<String>
Pattern.compile("\\w+").splitAsStream(s)     // tokeniser
```

### Intermediate operations (return a `Stream<T>`)

```java
.filter(predicate)            // keep matching
.map(fn)                      // T -> R
.flatMap(fn)                  // T -> Stream<R> and flatten
.mapToInt / mapToLong / mapToDouble   // to a primitive stream
.distinct()                   // stateful
.sorted()                     // stateful, natural order
.sorted(comparator)           // stateful, custom order
.peek(consumer)               // for debugging
.limit(n)                     // short-circuit
.skip(n)                      // short-circuit
.takeWhile(p)                 // short-circuit (Java 9+)
.dropWhile(p)                 // (Java 9+)
```

### Terminal operations (close the stream)

```java
.collect(Collectors.toList())         // -> List<T>   (use .toList() in Java 16+)
.collect(Collectors.toSet())          // -> Set<T>
.collect(Collectors.toMap(k, v))      // -> Map<K, V>
.collect(Collectors.groupingBy(k))    // -> Map<K, List<T>>
.collect(Collectors.partitioningBy(p))// -> Map<Boolean, List<T>>
.collect(Collectors.joining(", "))    // -> String
.toList() / .toSet() / .toMap(...)    // Java 16+ shortcuts
.count()                              // long
.sum() / .average() / .min() / .max() // on primitive streams only
.findFirst() / .findAny()             // Optional<T>
.anyMatch(p) / .allMatch(p) / .noneMatch(p)   // boolean
.forEach(consumer)                    // side-effecting
.reduce(identity, accumulator)        // fold
```

## 5. `Collectors` — the workhorses

```java
// Group by key
Map<Department, List<Employee>> byDept =
    employees.stream().collect(Collectors.groupingBy(Employee::department));

// Count by group
Map<Department, Long> counts =
    employees.stream().collect(Collectors.groupingBy(Employee::department, Collectors.counting()));

// Sum a property
Map<Department, BigDecimal> payroll =
    employees.stream().collect(Collectors.groupingBy(
        Employee::department,
        Collectors.reducing(BigDecimal.ZERO, Employee::salary, BigDecimal::add)));

// Partition by predicate
Map<Boolean, List<Integer>> evenOdd =
    nums.stream().collect(Collectors.partitioningBy(n -> n % 2 == 0));

// Build a Map
Map<String, User> byId =
    users.stream().collect(Collectors.toMap(User::id, u -> u));

// Join to a String
String csv = rows.stream().map(Row::toCsv).collect(Collectors.joining(",\n"));
```

## 6. Primitive streams — `IntStream`, `LongStream`, `DoubleStream`

The boxed `Stream<Integer>` is wasteful for arithmetic. Use the primitive
streams:

```java
IntStream.range(0, 10)             // 0..9
IntStream.rangeClosed(1, 6)       // 1..6
IntStream.of(1, 2, 3).sum()        // 6
IntStream.of(1, 2, 3).average()    // OptionalDouble[2.0]
int sum = stream.mapToInt(String::length).sum();
```

`Stream<Integer>` → `IntStream`: `.mapToInt(Integer::intValue)`.
`IntStream` → `Stream<Integer>`: `.boxed()`.

## 7. `Optional<T>`

A container that may or may not hold a non-null value. The replacement
for `null` returns.

```java
Optional<User> findById(long id) { /* ... */ }

User user = findById(42).orElseThrow(() -> new NoSuchElementException(id));
String name = findById(42).map(User::name).orElse("(unknown)");
findById(42).ifPresent(u -> sendEmail(u));
findById(42).ifPresentOrElse(this::sendEmail, () -> log("not found"));
```

**Rules:**
- **Use `Optional` for *return types*; never for fields or parameters.**
- Never call `.get()` without first checking `.isPresent()`.
- `Optional.of(null)` throws; `Optional.ofNullable(t)` allows null.
- `Optional` has no place in a `List` or a `Map` value.

`Stream` operations `findFirst`, `findAny`, `reduce`, `min`, `max`,
`average` return `Optional` for exactly the right reason.

## 8. `Optional` and streams together

```java
Optional<Order> latest = orders.stream()
        .max(Comparator.comparing(Order::placedAt));
String id = latest.map(Order::id).orElse("(none)");
```

`Optional.flatMap` is the trick for "chained" lookups:
```java
Optional<Address> addr = findUser(42).flatMap(User::primaryAddress);
```

## 9. Method references vs. lambdas — when to use which

- Use a method reference when it's **shorter and equally clear**:
  `String::length` over `s -> s.length()`.
- Use a lambda when you need a **block** or **local logic**:
  `(a, b) -> a.createdAt().compareTo(b.createdAt())`.

## 10. What *not* to do with streams

- Don't use a stream when a `for` loop is clearer (complex state machines).
- Don't throw checked exceptions from inside a lambda in a stream.
  Streams amplify the pain; use unchecked wrappers.
- Don't mutate external state from `map`/`filter`. Streams favour
  pure functions; side effects make debugging painful.
- Don't assume `.parallelStream()` is faster. For small data sets or
  expensive spliterators, it's slower. **Measure**.
- Don't store a stream in a field; consume it within the method.
  Streams are single-use.

## 11. Lambdas and `final` / "effectively final"

A lambda captures local variables. For this to work, the variable must
be **effectively final** (its value doesn't change after initialisation).

```java
int threshold = 10;
list.stream().filter(x -> x > threshold);  // OK; threshold is effectively final
threshold = 20;                            // nope — no longer effectively final
```

The reason: the lambda may run long after the method has returned, and
Java doesn't want a surprise-shared mutable variable.

Instance fields don't have this restriction — they're captured via
`this`, and changes to them *are* visible.

---

## Do the lab

Build a small `Orders` domain and exercise lambdas, method references,
and the most useful stream operators. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

functional interface · `@FunctionalInterface` · `Function` · `Consumer` ·
`Supplier` · `Predicate` · `UnaryOperator` · lambda · method reference ·
`Stream` · intermediate / terminal · `collect` · `Collectors` · `groupingBy` ·
`partitioningBy` · `Optional` · primitive streams · parallel stream ·
effectively final

**Next →** [Module 08: Exceptions, `try`-with-resources & `Optional`](../08-exceptions-optional/)

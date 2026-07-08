# Module 05 — Generics & Type Parameters

**Goal:** write generic classes, interfaces, and methods that are
**type-safe by construction** — catching whole categories of bugs at
compile time. Master bounded types, wildcards, and the **PECS** rule.
Understand type erasure and the limits it imposes.

⏱️ ~3 h · 🎯 Prereq: Module 04.

---

## 1. The point of generics

A list of strings and a list of integers should not be the same type. The
JDK's solution: parameterise the list by its element type.

```java
List<String> names = new ArrayList<String>();
List<Integer> ages  = new ArrayList<Integer>();
```

Before generics (Java 1.4 and earlier), the list was a `List` of `Object`,
and every read needed an unchecked cast. Generics move that cast from
**runtime to compile time** — the type checker catches the error before
the program runs.

```java
List<String> names = new ArrayList<>();
names.add("Ada");                  // OK
names.add(42);                     // compile error: Integer cannot be converted to String
String first = names.get(0);       // no cast needed
```

## 2. Generic classes

A class can declare one or more **type parameters** in its header. The
parameters are placeholders filled in when the class is used.

```java
public final class Box<T> {
    private T value;
    public Box(T initial) { this.value = initial; }
    public T get()       { return value; }
    public void set(T v) { this.value = v; }
}

Box<String> b = new Box<>("hi");
b.get();           // String
```

Convention: `T` (type), `E` (element), `K`/`V` (key/value), `R` (return),
`N` (number), `?` (unknown).

## 3. Generic interfaces

```java
public interface Comparable<T> {
    int compareTo(T other);
}

public final class Money implements Comparable<Money> {
    private final long cents;
    @Override public int compareTo(Money other) { return Long.compare(cents, other.cents); }
}
```

The implementing class declares the *type argument* for `T` (here, `Money`).
This is what lets `List<Money>.sort()` work without casts.

## 4. Generic methods

A method can be generic independently of its class:
```java
public static <T> T first(List<T> xs) {
    return xs.isEmpty() ? null : xs.get(0);
}
```

The `<T>` is **mandatory** when the type is a *method-scoped* type
parameter. It's omitted when `T` is already declared on the class.

```java
public final class Box<T> {
    public <U> Box<U> pairWith(U other) { /* method-level U, instance-level T */ }
}
```

## 5. Bounded types — `<T extends X>`

Limit what `T` can be:

```java
public static <T extends Comparable<T>> T max(Collection<T> xs) {
    return xs.stream().max(Comparator.naturalOrder()).orElseThrow();
}
```

The bound is a *contract* — only `T`s that are `Comparable<T>` may be
used. The compiler will then let you call `T.compareTo` inside the method.

**Multiple bounds:** `<T extends A & B>` (the leftmost bound is used as
the erasure).

```java
public static <T extends Number & Comparable<T>> T sum(Collection<T> xs) {
    T acc = xs.iterator().next();
    for (T x : xs) if (x.compareTo(acc) > 0) acc = x;
    return acc;
}
```

## 6. Wildcards `?` — when you don't know or care

Sometimes you don't need the *exact* type — any subtype will do:

```java
public static double totalArea(List<? extends Shape> shapes) {
    return shapes.stream().mapToDouble(Shape::area).sum();
}
```

`? extends Shape` means "some unknown subtype of `Shape`." You can
**read** `Shape` values out, but you **cannot add** anything to the list
— you don't know the exact element type, so the compiler can't guarantee
type safety.

There are three forms:
- `?` (or `<?>`) — any type.
- `<? extends T>` — some subtype of `T` (read as "T or below").
- `<? super T>` — some supertype of `T` (read as "T or above").

## 7. PECS — producer extends, consumer super

Joshua Bloch's rule for picking the right wildcard:

> **Use `? extends T` when the structure *produces* `T` values (you read
> them out). Use `? super T` when the structure *consumes* `T` values
> (you write them in).**

```java
// PRODUCER: the source produces T values.
public static <T> void copy(List<? extends T> src, List<? super T> dst) {
    for (T t : src) dst.add(t);
}

List<Integer> src = List.of(1, 2, 3);
List<Number>  dst = new ArrayList<>();
copy(src, dst);   // src ? extends Integer, dst ? super Integer (and Number is a super)
```

The JDK's `Collections.copy`, `Stream.collect`, and the constructor of
`ArrayList(Collection<? extends E>)` all use PECS.

**Memory aid:**
- *extends* → you can **get** values out.
- *super* → you can **put** values in.

## 8. Type erasure — the catch

Java's generics are implemented by **erasure**: at the JVM level,
`List<String>` and `List<Integer>` are the same class (`List`). The
compiler checks the types; the runtime doesn't know them.

Consequences:
- `new T()` — illegal; the runtime can't create a `T`.
- `new T[10]` — illegal; same reason.
- `instanceof List<String>` — illegal; the runtime sees only `List`.
- You can have **one** static field per raw class, not per `T`.

```java
public final class Box<T> {
    private final T value;
    public Box(T v) { this.value = v; }
    public T get()  { return value; }
    // Illegal:
    // public static T staticField;   // type parameters don't exist at runtime
    // public Box<T>[] array;         // can't create a generic array
}
```

The reason for erasure: backwards compatibility with pre-Java-5 code.
Other JVM languages (Scala, Kotlin) reify generics, but pay the
compatibility price differently.

## 9. Generic methods vs. wildcards

- A **generic method** declares `<T>` and can refer to `T` in both the
  parameter list and the return type.
- A **wildcard** is a *use-site* "some unknown type" — the method itself
  is non-generic.

```java
// generic method: T is in scope, can be returned
public static <T> List<T> singletonList(T t) { return List.of(t); }

// wildcard: '?' is unknown, can be used but not named
public static int size(List<?> xs) { return xs.size(); }
```

When a type variable appears **only once** in the method signature,
prefer a wildcard — it makes the intent clearer.

## 10. Inheritance with generics

`List<Integer>` is **not** a `List<Number>`. Generics are *invariant*:
`List<Integer>` is a subtype of `List<? extends Integer>`, not of
`List<Number>`. Why? Because a `List<Number>` could accept a `Double`,
and an `Integer` list must not.

```java
List<Integer> ints = List.of(1, 2, 3);
List<Number>  nums = ints;         // compile error
List<Number>  nums = new ArrayList<>(ints);  // OK
```

Arrays are *covariant* (`Integer[]` IS-A `Number[]`) — and that's the
source of the famous `ArrayStoreException`:
```java
Integer[] xs = {1, 2, 3};
Object[] os = xs;          // legal (covariant arrays)
os[0] = "oops";            // throws ArrayStoreException at runtime
```
Generics fix this by being **invariant** — the unsafe code doesn't
compile.

## 11. Restrictions

A few things you cannot do:
- `new T()`, `new T[N]`, `T[].class`.
- `instanceof List<String>`.
- A generic class can't subclass `Throwable` directly (you can subclass
  `Throwable` *generically*, e.g. `class Box<T> extends Exception`).
- Static fields/methods can't reference the enclosing class's type
  parameter.
- A class can't have two `static` methods whose erasures are the same.

## 12. A worked example: a generic `Pair<K, V>`

```java
public record Pair<K, V>(K key, V value) {
    public static <K, V> Pair<K, V> of(K k, V v) { return new Pair<>(k, v); }

    // PECS: src is a producer, dst is a consumer.
    public static <K, V> void putIfAbsent(Map<K, V> map, Pair<? extends K, ? extends V> p) {
        map.putIfAbsent(p.key(), p.value());
    }
}
```

## 13. When *not* to use generics

- If your type has only one logical "form," generics add noise.
- If the type parameter would appear only in a field, the type is *better
  written as a generic*, but not if the operation is too narrow.
- If you find yourself sprinkling `@SuppressWarnings("unchecked")` — you
  may be working around a missing abstraction.

---

## Do the lab

Build a tiny generic `Pair` and a generic `Result` map, then apply PECS
in a small algorithm. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

generic class · type parameter · bound (`extends`) · wildcard `?` · `? extends
T` · `? super T` · PECS · type erasure · invariant · `<T>` on a method ·
`Comparable<T>` · raw type

**Next →** [Module 06: Collections Deep Dive](../06-collections-deep-dive/)

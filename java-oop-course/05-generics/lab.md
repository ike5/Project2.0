# Lab 05 — Generics Hands-On

**You'll:** build a small generic `Pair`, a generic `Result`-aware map
operation, and a small algorithm that uses PECS. ⏱️ ~55 min.

---

## Part A — Set up

```bash
mkdir -p ~/dev/oop05 && cd ~/dev/oop05
mkdir -p src/com/example/collections
```

## Part B — A generic `Pair`

`src/com/example/collections/Pair.java`:
```java
package com.example.collections;

public record Pair<K, V>(K key, V value) {
    public Pair {
        if (key == null) throw new IllegalArgumentException("key required");
    }
    public static <K, V> Pair<K, V> of(K key, V value) { return new Pair<>(key, value); }

    public static <K, V> void putIfAbsent(
            java.util.Map<K, V> map, Pair<? extends K, ? extends V> entry) {
        map.putIfAbsent(entry.key(), entry.value());
    }
}
```

Compile:
```bash
javac -d out $(find src -name '*.java')
```

✅ The `putIfAbsent` signature uses **PECS**: the `Pair` is *both* a
producer (we read `key` and `value` from it) and a consumer (we pass it
in), but each `? extends` bound is what allows a `Pair<String, Number>`
to be passed to a `Map<Object, Object>`.

## Part C — A bounded `max` function

`src/com/example/collections/Algorithms.java`:
```java
package com.example.collections;

import java.util.Collection;
import java.util.Comparator;

public final class Algorithms {
    private Algorithms() {}

    public static <T extends Comparable<T>> T max(Collection<T> xs) {
        if (xs.isEmpty()) throw new IllegalArgumentException("empty");
        T best = xs.iterator().next();
        for (T x : xs) if (x.compareTo(best) > 0) best = x;
        return best;
    }

    public static <T> T max(Collection<T> xs, Comparator<T> cmp) {
        if (xs.isEmpty()) throw new IllegalArgumentException("empty");
        T best = xs.iterator().next();
        for (T x : xs) if (cmp.compare(x, best) > 0) best = x;
        return best;
    }
}
```

## Part D — PECS in a `copy` method

`src/com/example/collections/Copy.java`:
```java
package com.example.collections;

import java.util.List;

public final class Copy {
    private Copy() {}

    // src produces T, dst consumes T.
    public static <T> void copy(List<? extends T> src, List<? super T> dst) {
        for (T t : src) dst.add(t);
    }
}
```

`src/com/example/collections/Main.java`:
```java
package com.example.collections;

import java.util.ArrayList;
import java.util.List;

public class Main {
    public static void main(String[] args) {
        // Pair
        var entry = Pair.of("answer", 42);
        System.out.println(entry);

        var bag = new java.util.HashMap<String, Number>();
        Pair.putIfAbsent(bag, Pair.<String, Integer>of("answer", 42));
        Pair.putIfAbsent(bag, Pair.<String, Double>of("pi", 3.14));
        System.out.println(bag);

        // Algorithms.max
        System.out.println(Algorithms.max(List.of(3, 1, 4, 1, 5, 9, 2, 6)));   // 9
        // Use more differentiating data:
        var names = List.of("Ada", "Grace", "Alan");
        System.out.println(Algorithms.max(names, (a, b) -> Integer.compare(a.length(), b.length()))); // "Grace"

        // Copy with PECS
        List<Integer> src = List.of(1, 2, 3);
        List<Number>  dst = new ArrayList<>();
        Copy.copy(src, dst);
        System.out.println(dst);     // [1, 2, 3]
    }
}
```

Compile + run:
```bash
javac -d out $(find src -name '*.java')
java -cp out com.example.collections.Main
```

Expected:
```
Pair[key=answer, value=42]
{answer=42, pi=3.14}
9
Grace
[1, 2, 3]
```

✅ Watch the `Pair.putIfAbsent` calls — the compiler accepts both
`Pair<String, Integer>` and `Pair<String, Double>` because of the
`? extends K` and `? extends V` wildcards.

## Part E — Type erasure in action

Add a quick demonstration:
```java
// Both lists are the same class at runtime.
List<String>  ss = new ArrayList<>();
List<Integer> is = new ArrayList<>();
System.out.println(ss.getClass() == is.getClass());    // true
System.out.println(ss instanceof List);                // true
// System.out.println(ss instanceof List<String>);     // compile error: illegal
```

This is the type erasure rule: the JVM doesn't know the element type.

## What you learned

- Generics move "this could be the wrong type" from runtime to compile
  time.
- `<T extends X>` bounds what `T` can be; use the bound's methods inside
  the generic.
- `? extends T` (read-only) and `? super T` (write-only) are the
  wildcard rules — **PECS**.
- Generics are *invariant* — `List<Integer>` is not a `List<Number>`.
  This is what makes them safe.
- Type erasure means you can't `new T()`, `new T[N]`, or check
  `instanceof List<String>`.

➡️ **[challenge.md](./challenge.md)** then [Module 06](../06-collections-deep-dive/).

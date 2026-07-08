# Lab 06 — Pick the Right Collection

**You'll:** build a small `Index<K, V>` and exercise `Map`, `List`, and
`Deque` idioms. ⏱️ ~45 min.

---

## Part A — Set up

```bash
mkdir -p ~/dev/oop06 && cd ~/dev/oop06
mkdir -p src/com/example/registry
```

## Part B — Build a small `Index<K, V>`

`src/com/example/registry/Index.java`:
```java
package com.example.registry;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class Index<K, V> {
    private final Map<K, List<V>> byKey = new HashMap<>();

    public void add(K key, V value) {
        byKey.computeIfAbsent(key, k -> new ArrayList<>()).add(value);
    }

    public List<V> get(K key) {
        return Collections.unmodifiableList(byKey.getOrDefault(key, List.of()));
    }

    public Set<K> keys() { return Collections.unmodifiableSet(byKey.keySet()); }

    public int size() { return byKey.size(); }
}
```

## Part C — Driver

`src/com/example/registry/Main.java`:
```java
package com.example.registry;

import java.util.ArrayDeque;
import java.util.Comparator;
import java.util.Deque;
import java.util.List;
import java.util.PriorityQueue;

public class Main {
    public static void main(String[] args) {
        // Index — the canonical computeIfAbsent pattern.
        Index<String, String> byAuthor = new Index<>();
        byAuthor.add("Ada", "On the Analytical Engine");
        byAuthor.add("Ada", "Notes on the Bernoulli Numbers");
        byAuthor.add("Grace", "On a New Programming Language");
        byAuthor.add("Grace", "The Linker");

        byAuthor.keys().forEach(k ->
                System.out.println(k + " -> " + byAuthor.get(k)));

        // ArrayDeque as a stack.
        Deque<Integer> stack = new ArrayDeque<>();
        for (int x : List.of(1, 2, 3)) stack.push(x);
        while (!stack.isEmpty()) System.out.print(stack.pop() + " ");
        System.out.println();

        // PriorityQueue: smallest first.
        PriorityQueue<Integer> pq = new PriorityQueue<>();
        for (int x : List.of(5, 1, 3, 2, 4)) pq.offer(x);
        while (!pq.isEmpty()) System.out.print(pq.poll() + " ");
        System.out.println();

        // Comparator chaining.
        record Person(String name, int age) {}
        var people = new ArrayList<Person>(List.of(
                new Person("Ada", 36),
                new Person("Grace", 85),
                new Person("Alan", 41)));
        people.sort(Comparator.comparingInt(Person::age).thenComparing(Person::name));
        people.forEach(System.out::println);
    }
}
```

Compile + run:
```bash
javac -d out $(find src -name '*.java')
java -cp out com.example.registry.Main
```

Expected (key order is *not* guaranteed — `HashMap` iteration is
implementation-defined):
```
Ada -> [On the Analytical Engine, Notes on the Bernoulli Numbers]
Grace -> [On a New Programming Language, The Linker]
3 2 1
1 2 3 4 5
Person[name=Ada, age=36]
Person[name=Alan, age=41]
Person[name=Grace, age=85]
over = 1
the = 2
...
```

(The `Index.keys()` order is *not* guaranteed — `HashMap` iteration
order is implementation-defined. If you need insertion order, use
`LinkedHashMap`.)

✅ Note that `Index.keys()` returns an *unmodifiable view*: the caller
can't `add` to it without an exception.

## Part D — Demonstrate the iteration pitfall

Add a quick driver to `Main` (commented out) that *demonstrates* a
`ConcurrentModificationException`:

```java
var list = new java.util.ArrayList<>(List.of(1, 2, 3, 4, 5));
for (Integer x : list) {
    if (x % 2 == 0) list.remove(x);     // throws CME
}
```

Run, observe the exception. Then fix it with `removeIf`:
```java
list.removeIf(x -> x % 2 == 0);
```

## Part E — A `Map.merge` pipeline

Add to `Main`:
```java
String text = "the quick brown fox jumps over the lazy dog";
Map<String, Long> counts = new java.util.HashMap<>();
for (String w : text.split(" ")) {
    counts.merge(w, 1L, Long::sum);
}
counts.forEach((k, v) -> System.out.println(k + " = " + v));
```

`merge` is the cleanest "increment a counter" idiom in Java.

## What you learned

- `ArrayList` for lists, `HashSet` for sets, `HashMap` for maps,
  `ArrayDeque` for stacks/queues.
- `computeIfAbsent` for "create bucket if missing, add to it."
- `Comparator.comparingInt(...).thenComparing(...)` for fluent ordering.
- `List.of` / `Set.of` / `Map.of` for immutable literals.
- Don't mutate a collection while iterating; use `removeIf` or an iterator's
  `remove`.

➡️ **[challenge.md](./challenge.md)** then [Module 07](../07-lambdas-streams/).

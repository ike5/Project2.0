# Module 06 — Collections Deep Dive

**Goal:** pick the right collection for each job, write `Comparator`s fluently,
and avoid the common mistakes (`LinkedList` for stacks, `Vector`,
synchronized wrappers, mutating while iterating).

⏱️ ~2.5 h · 🎯 Prereq: Module 05.

---

## 1. The big picture

```
                    Iterable<T>
                        |
                    Collection<T>
        ________________|________________
       |          |             |             |
     List<T>    Set<T>       Queue<T>     (Map is separate)
                       |
                  SortedSet<T>
```

`Map<K, V>` is **not** a `Collection`; it pairs keys with values. Iterate
it via `entrySet()`, `keySet()`, or `values()`.

The full picture is in **[cheatsheets/collections.md](../cheatsheets/collections.md)**.
This module focuses on the *defaults* and the *trade-offs*.

## 2. The "just use this" defaults

| You need… | Reach for… |
|-----------|------------|
| A list of things, append, iterate | `ArrayList` |
| A set of things, no duplicates | `HashSet` |
| A map of keys to values | `HashMap` |
| A stack or a queue | `ArrayDeque` |
| The smallest item first | `PriorityQueue` |
| Iteration in insertion order | `LinkedHashSet` / `LinkedHashMap` |
| Iteration in sorted order | `TreeSet` / `TreeMap` |
| A set/map of enum values | `EnumSet` / `EnumMap` |
| A multi-threaded map | `ConcurrentHashMap` |
| An immutable list/set/map | `List.of` / `Set.of` / `Map.of` |

If you default to `ArrayList`, `HashSet`, and `HashMap` you'll be right
80% of the time.

## 3. The legacy traps to avoid

- **`Vector`, `Stack`, `Hashtable`** — synchronised legacy classes; use
  `ArrayList`, `ArrayDeque`, and `ConcurrentHashMap` instead.
- **`Collections.synchronizedList(new ArrayList<>())`** — slow; use
  `ConcurrentHashMap` for maps, and for lists either accept the
  contention or use a copy-on-write variant.
- **`LinkedList` for queues and stacks** — `ArrayDeque` is faster in
  practice. `LinkedList` is mostly a "linked-list data structure" class
  with `Deque` bolted on; the constant factors are bad.
- **Mutating a collection while iterating** — `ConcurrentModificationException`.
  Use iterators' `remove`, or `removeIf`, or collect to a new collection.

## 4. `List` — the four operations that matter

```java
list.add(e);                          // append
list.add(idx, e);                     // insert (O(n))
list.get(idx);                        // O(1) for ArrayList, O(n) for LinkedList
list.remove(idx);                     // O(n)
list.set(idx, e);                     // replace
list.indexOf(e);                      // linear scan
list.contains(e);                     // uses equals
list.subList(from, to);               // view (changes to view affect the list)
list.sort(comparator);                // in-place
```

For `ArrayList`, the backing array grows by ~1.5x when full. So `add` is
amortised O(1).

## 5. `Set` — uniqueness by `equals`

The `Set` contract is "no duplicates by `equals`." Most implementations
also require that elements' `hashCode` is consistent with `equals`
(`HashSet`) — or that they're `Comparable` (`TreeSet`).

```java
Set<String> tags = new HashSet<>();
tags.add("java");
tags.add("java");        // ignored
tags.add("Java");        // added (different String)
```

**`LinkedHashSet`** preserves insertion order. **`TreeSet`** sorts by
natural order (the elements are `Comparable`) or by a `Comparator`. Both
have O(log n) `add` and `contains`; `HashSet` has O(1) average.

## 6. `Map` — the four methods to know

Most "I need to update a map" patterns reduce to four method calls:
- `map.getOrDefault(key, fallback)`
- `map.putIfAbsent(key, value)` — atomic if absent
- `map.computeIfAbsent(key, fn)` — compute and store only if absent
- `map.merge(key, value, remappingFn)` — atomic update with a combiner

```java
// Word-count:
Map<String, Long> counts = new HashMap<>();
for (String w : words) counts.merge(w, 1L, Long::sum);

// Index by id:
Map<String, User> byId = users.stream().collect(Collectors.toMap(User::id, u -> u));

// Group by some key:
Map<Department, List<Employee>> byDept = employees.stream()
        .collect(Collectors.groupingBy(Employee::department));
```

Iterate a `Map` as `entrySet` for both key and value:
```java
for (var e : map.entrySet()) {
    String k = e.getKey(); Integer v = e.getValue();
    // ...
}
```

## 7. `Queue` / `Deque` — FIFO, LIFO, both

A **queue** is FIFO: you `offer` to the back, `poll` from the front.
A **deque** is double-ended; you can also `push`/`pop` at the head for a
stack.

```java
Deque<Task> stack = new ArrayDeque<>();
stack.push(task);          // top of stack
Task top = stack.pop();    // top of stack, throws if empty
Task peek = stack.peek();  // top of stack, null if empty

Queue<Task> queue = new ArrayDeque<>();
queue.offer(task);
Task next = queue.poll();
```

`push`/`pop` and `offer`/`poll` throw vs. return special values; the
throw-on-fail methods are `add`, `remove`, `element`.

For priority-based ordering, use `PriorityQueue`:
```java
Queue<Task> byPriority = new PriorityQueue<>(Comparator.comparingInt(Task::priority));
byPriority.offer(low);
byPriority.offer(high);
byPriority.poll();   // high
```

`PriorityQueue` is a **binary heap** — O(log n) `add`/`poll`, O(1) `peek`.

## 8. `Comparator` — fluent ordering

`Comparator` is a `@FunctionalInterface`; lambdas are everywhere:
```java
Comparator<User> byAge    = Comparator.comparingInt(User::age);
Comparator<User> byName   = Comparator.comparing(User::name);
Comparator<User> byAgeDesc = Comparator.comparingInt(User::age).reversed();

// Nulls first/last
Comparator<User> byNameNullsLast = Comparator.comparing(User::name, Comparator.nullsLast(Comparator.naturalOrder()));

// Chained: primary, secondary
Comparator<User> byAgeThenName =
        Comparator.comparingInt(User::age).thenComparing(User::name);
```

`Comparable` is the *natural* order; `Comparator` is *any* order.

## 9. Iteration patterns

```java
// enhanced for
for (var e : list) { /* ... */ }

// iterator (only place you can `remove`):
for (var it = list.iterator(); it.hasNext(); ) {
    var e = it.next();
    if (bad(e)) it.remove();
}

// stream (declarative, lazy)
list.stream().filter(this::good).map(this::transform).forEach(this::handle);

// parallel stream (only when the work is CPU-bound and the data is large)
list.parallelStream().filter(...).forEach(...);

// forEach on collections (Java 8+)
list.forEach(System.out::println);
```

**Don't** mix: if you're iterating with an enhanced for, do *not* call
`list.add` or `list.remove` inside the body. The `ConcurrentModificationException`
will hit eventually, and it's painful to debug.

## 10. Empty and singleton collections

`List.of()` (no args) is an empty immutable list. `Map.of()` similarly.
The JDK's `Collections.emptyList()` and friends do the same. Use these
instead of returning `null` from methods that should return a list — the
caller can iterate without checking.

## 11. Unmodifiable views

`Collections.unmodifiableList(c)` returns a *view* that throws on
mutation. Useful for *exposing* a private collection without risking
external mutation:

```java
public final class Team {
    private final List<String> members = new ArrayList<>();
    public List<String> members() { return Collections.unmodifiableList(members); }
    public void add(String m) { members.add(m); }
}
```

The view is *live* — changes to the underlying list are visible through
the view. (Compare to `List.copyOf(c)`, which is a true immutable copy.)

## 12. Thread-safety at a glance

For a single thread, the default collections are fine. For multiple
threads:

- **`ConcurrentHashMap`** — the right answer for a shared map. Allows
  concurrent reads and writes; iterators are weakly consistent.
- **`CopyOnWriteArrayList`** — for a list that's read often and written
  rarely (e.g. a list of listeners). Writes copy the whole backing array.
- **`ArrayDeque` is *not* thread-safe.** Wrap with `Collections.synchronizedDeque`
  if you must, but a producer-consumer `BlockingQueue` is the proper
  answer.
- **`PriorityBlockingQueue`** — a thread-safe priority queue.

Don't reach for `synchronized` on a `HashMap`. It's slow and easy to get
wrong. The `Concurrent*` classes are designed by experts.

## 13. The `equals`/`hashCode` contract — applied

If you put a custom class into a `HashMap` / `HashSet` and override
`equals`, you **must** override `hashCode` too. Two equal objects must
have the same hash. If they don't, the map silently loses entries.

```java
public final class Point {
    private final int x, y;
    @Override public int hashCode() { return Objects.hash(x, y); }
    @Override public boolean equals(Object o) {
        return o instanceof Point p && x == p.x && y == p.y;
    }
}
```

`Objects.hash(...)` builds a hash from the fields; it's adequate for most
classes. For performance-critical classes, compute the hash lazily and
cache it.

## 14. A worked example — a simple `Index<K, V>`

```java
public final class Index<K, V> {
    private final Map<K, List<V>> byKey = new HashMap<>();

    public void add(K key, V value) {
        byKey.computeIfAbsent(key, k -> new ArrayList<>()).add(value);
    }

    public List<V> get(K key) {
        return Collections.unmodifiableList(byKey.getOrDefault(key, List.of()));
    }

    public Set<K> keys() { return Collections.unmodifiableSet(byKey.keySet()); }
}
```

`computeIfAbsent` is the canonical idiom for "make the bucket if missing,
add to it." The accessors return *unmodifiable views* — the caller can't
silently corrupt the index.

---

## Do the lab

Build a small `Index<K, V>` and exercise the collections framework.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

`Collection` · `List` / `Set` / `Queue` / `Deque` · `Map` · `ArrayList` ·
`HashSet` / `HashMap` / `TreeSet` / `TreeMap` · `LinkedHashSet` / `LinkedHashMap` ·
`EnumSet` / `EnumMap` · `ArrayDeque` / `PriorityQueue` · `Comparator` ·
`Comparable` · `ConcurrentHashMap` · `List.of` / `Map.of` / `Set.of` ·
`Collections.unmodifiableList` · `computeIfAbsent` · `merge`

**Next →** [Module 07: Lambdas, Streams & Functional Interfaces](../07-lambdas-streams/)

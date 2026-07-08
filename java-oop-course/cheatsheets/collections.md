# Java Collections Cheatsheet

Pick the right type. The wrong choice is rarely a bug — it's just *slow* or
*bug-prone*.

## The big picture

```
                       Iterable<T>
                           |
                        Collection<T>
            ________________|________________
           |          |              |            |
         List<T>    Set<T>        Queue<T>     (Map is separate)
                       |
                  SortedSet<T>
```

`Map<K, V>` is **not** a `Collection`; it maps keys to values. `Map.entrySet()`
gives you a `Set<Entry<K, V>>` to iterate keys/values together.

## List — ordered, allows duplicates

| Class | Backing | Get | Add at end | Add in middle | Notes |
|-------|---------|-----|-----------|--------------|-------|
| `ArrayList` | array | O(1) | O(1) amort. | O(n) | Default. Fast random access. |
| `LinkedList` | doubly-linked list | O(n) | O(1) | O(1) at iterator | Avoid for most uses; use `ArrayDeque`. |
| `List.copyOf(c)` | immutable copy | O(1) | — | — | Use for read-only lists. |
| `List.of(...)` | immutable literal | O(1) | — | — | No nulls. |

Pick **`ArrayList`** by default. Use `Arrays.asList(...)` only for fixed-size
backed views of an array.

## Set — unique elements

| Class | Backing | add/contains | Order | Notes |
|-------|---------|--------------|-------|-------|
| `HashSet` | hash table | O(1) | none | Default. |
| `LinkedHashSet` | hash + linked list | O(1) | insertion | Preserves insertion order. |
| `TreeSet` | red-black tree | O(log n) | sorted | Requires `Comparable` or `Comparator`. |
| `EnumSet` | bit vector | O(1) | enum order | The right answer for sets of enums. |
| `Set.copyOf`/`Set.of` | immutable | O(1) | — | |

## Map — keys to values

| Class | Backing | get/put | Order | Notes |
|-------|---------|---------|-------|-------|
| `HashMap` | hash table | O(1) | none | Default. Allows one null key. |
| `LinkedHashMap` | hash + linked list | O(1) | insertion or access | Cache-friendly. |
| `TreeMap` | red-black tree | O(log n) | sorted by key | |
| `EnumMap` | array | O(1) | enum order | The right answer for maps keyed by enums. |
| `Map.copyOf`/`Map.of` | immutable | O(1) | — | |
| `ConcurrentHashMap` | segmented hash | O(1) | none | Thread-safe, scales. |

`getOrDefault`, `putIfAbsent`, `computeIfAbsent`, `merge` are the four
methods to know — they save you from a *lot* of `containsKey`/`get` patterns.

## Queue / Deque — FIFO, LIFO, both

| Class | Use for | Notes |
|-------|---------|-------|
| `ArrayDeque<T>` | stack, queue | Preferred over `Stack` and `LinkedList`. O(1) at both ends. |
| `LinkedList<T>` | rare | Implements `Deque` but `ArrayDeque` is faster. |
| `PriorityQueue<T>` | min/max heap | O(log n) `add`/`poll`. Head is the smallest by natural order or comparator. |
| `ArrayBlockingQueue<T>` | bounded producer-consumer | Backed by an array; thread-safe. |

```java
Deque<String> stack = new ArrayDeque<>();
stack.push("a");        // push
String top = stack.pop();   // pop

Queue<Task> pending = new ArrayDeque<>();
pending.offer(task);
Task next = pending.poll();   // returns null if empty
```

## When to use what

- "I need an ordered list, I'll append to the end and iterate." → `ArrayList`.
- "I need a stack or a queue." → `ArrayDeque`.
- "I need a set with constant-time contains." → `HashSet`.
- "I need to iterate the set in insertion order." → `LinkedHashSet`.
- "I need to iterate the set in sorted order." → `TreeSet`.
- "I need to look up by key." → `HashMap`.
- "I need a key-value map sorted by key." → `TreeMap`.
- "I need a key-value map with insertion order." → `LinkedHashMap`.
- "I'm processing the smallest item first." → `PriorityQueue`.
- "I'm doing this in a thread-safe way." → `ConcurrentHashMap`,
  `ConcurrentLinkedQueue`, `ConcurrentSkipListMap`.

## Things to avoid

- **`Vector`**, **`Stack`**, **`Hashtable`** — legacy, synchronised,
  generally replaced.
- **`Collections.synchronizedList(new ArrayList<>())`** — slow; use the
  `Concurrent*` collections instead.
- **Long-deprecated `Enumeration`** — use `Iterator` (or `Iterable`).
- **Mutating a collection while iterating** — use iterators' `remove` or
  collect to a new collection.
- **`TreeSet`/`TreeMap` with a mutable key** — modifying the key after
  insertion breaks the contract.
- **`double` as a `Map` key** without a custom `equals`/`hashCode` — the
  default doesn't work for `NaN` etc. Use `Double` with `Objects.hash` if
  you must, but consider `Map<Bucket, List<Value>>` instead.

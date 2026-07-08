# Challenge 06 — Collections

Solution in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Word-counting with `Map.merge`.** Given `String text`, build a
   `Map<String, Long>` of word → count, case-insensitive, ignoring
   punctuation. Use `Map.merge` (or `compute`).

2. **LRU cache with `LinkedHashMap`.** Implement a fixed-capacity
   `LruCache<K, V>` (extends `LinkedHashMap` with `removeEldestEntry`).
   Show that after exceeding capacity, the least-recently-inserted entry
   is evicted.

3. **A `MultiMap` (alias `Index<K, V>`).** Build a `MultiMap<K, V>` with
   `add(K, V)`, `get(K) -> List<V>`, `keys() -> Set<K>`, and
   `remove(K, V)`. Internally use `HashMap<K, List<V>>`. The returned
   `get(K)` list must be an unmodifiable view.

4. **`PriorityQueue` as a min-heap.** Build a `static List<Task> schedule(List<Task> tasks)`
   that returns the tasks in the order they should be processed (smallest
   deadline first), using `PriorityQueue`. `Task` has `String name` and
   `int deadline` (a small int = urgent).

5. **Choose the right collection.** For each scenario, name the
   collection and write a one-line explanation:
   - A "recent files" menu in an editor.
   - The set of unique words in a book (you also need alphabetical order).
   - A many-producer, many-consumer task queue with priorities.
   - A read-mostly list of subscribers that a publisher notifies.

## Success criteria

- [ ] Word count handles case and basic punctuation.
- [ ] `LruCache` evicts the eldest entry on overflow.
- [ ] `MultiMap` returns an unmodifiable view from `get`.
- [ ] `schedule` returns tasks in deadline order using `PriorityQueue`.
- [ ] You can justify each collection choice.

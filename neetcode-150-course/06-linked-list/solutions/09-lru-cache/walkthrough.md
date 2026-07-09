# LRU Cache - walkthrough

**Difficulty:** Medium &middot; **Module:** 06 Linked List

## Brief

Design a data structure that follows the constraints of a **Least Recently Used (LRU) cache**. Implement the `LRUCache` class with `get(key)` and `put(key, value)` methods, both running in O(1).

## Examples

- `LRUCache(2); put(1,1); put(2,2); get(1) -> 1; put(3,3); get(2) -> -1` &rarr; `1`

## Constraints

- 1 <= capacity <= 3000
- 0 <= key <= 10^4
- 0 <= value <= 10^5
- At most 2 * 10^5 calls to get and put

## Intuition

A **doubly linked list** of nodes plus a **hash map** from key to
node gives O(1) access (via the map) and O(1) reordering (via the list).

- `head` and `tail` are sentinels so we never have to null-check neighbors.
- `moveToFront(n)`: unlink `n`, then insert it after `head`.
- On `put`, if the cache is full, evict `tail.prev` (the LRU).

**Time:** O(1) per op. **Space:** O(capacity).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

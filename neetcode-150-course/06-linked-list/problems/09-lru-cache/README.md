# LRU Cache

**Difficulty:** Medium

## Problem

Design a data structure that follows the constraints of a **Least Recently Used (LRU) cache**. Implement the `LRUCache` class with `get(key)` and `put(key, value)` methods, both running in O(1).

## Examples

```
Input:  LRUCache(2); put(1,1); put(2,2); get(1) -> 1; put(3,3); get(2) -> -1
Output: 1
```

## Constraints

- 1 <= capacity <= 3000
- 0 <= key <= 10^4
- 0 <= value <= 10^5
- At most 2 * 10^5 calls to get and put

## Hints

1. Hash map from key to node + a doubly linked list of nodes in MRU-to-LRU order.
2. `get` moves the node to the front; `put` evicts from the back if over capacity.

## Solution

See [`../../solutions/09-lru-cache/`](../../solutions/09-lru-cache/) for the Python and Java 21 solutions and a step-by-step walkthrough.

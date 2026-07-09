# Time Based Key-Value Store - walkthrough

**Difficulty:** Medium &middot; **Module:** 05 Binary Search

## Brief

Design a time-based key-value data structure that can store multiple values for the same key at different time stamps and retrieve the key's value at a certain timestamp. Implement the `TimeMap` class with `set(key, value, timestamp)` and `get(key, timestamp)` methods.

## Examples

- `TimeMap(); set('foo','bar',1); get('foo',1) -> 'bar'; get('foo',3) -> 'bar' (no value at ts 3, use ts 1)` &rarr; `['bar','bar']`

## Constraints

- 1 <= key.length, value.length <= 100
- key and value consist of lowercase English letters and digits
- 1 <= timestamp <= 10^7
- set is called at most 2 * 10^5 times per test
- get is called at most 2 * 10^5 times per test

## Intuition

Two maps of lists: one for timestamps, one for values (kept in sync
by index). `get` binary-searches the timestamps for the largest one `<=`
the query, and returns the corresponding value (or `""` if no such
timestamp exists).

**Time:** O(log n) per `get`, O(1) amortized per `set`. **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

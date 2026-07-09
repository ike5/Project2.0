# Time Based Key-Value Store

**Difficulty:** Medium

## Problem

Design a time-based key-value data structure that can store multiple values for the same key at different time stamps and retrieve the key's value at a certain timestamp. Implement the `TimeMap` class with `set(key, value, timestamp)` and `get(key, timestamp)` methods.

## Examples

```
Input:  TimeMap(); set('foo','bar',1); get('foo',1) -> 'bar'; get('foo',3) -> 'bar' (no value at ts 3, use ts 1)
Output: ['bar','bar']
```

## Constraints

- 1 <= key.length, value.length <= 100
- key and value consist of lowercase English letters and digits
- 1 <= timestamp <= 10^7
- set is called at most 2 * 10^5 times per test
- get is called at most 2 * 10^5 times per test

## Hints

1. Per key, store a list of (timestamp, value), sorted by timestamp.
2. `get` is a binary search for the largest timestamp <= the query.

## Solution

See [`../../solutions/06-time-based-key-value-store/`](../../solutions/06-time-based-key-value-store/) for the Python and Java 21 solutions and a step-by-step walkthrough.

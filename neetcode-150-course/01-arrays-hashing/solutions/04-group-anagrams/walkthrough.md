# Group Anagrams - walkthrough

**Difficulty:** Medium &middot; **Module:** 01 Arrays Hashing

## Brief

Given an array of strings `strs`, group the anagrams together. You may return the groups in any order.

## Examples

- `strs = ['eat','tea','tan','ate','nat','bat']` &rarr; `[['bat'],['nat','tan'],['ate','eat','tea']]`
- `strs = ['']` &rarr; `[['']]`
- `strs = ['a']` &rarr; `[['a']]`

## Constraints

- 1 <= len(strs) <= 10^4
- 0 <= len(strs[i]) <= 100
- strs[i] consists of lowercase English letters

## Intuition

Anagrams become identical once sorted. So they share a *canonical form* (the
sorted string). Group by that.

## Approach
For each string, sort its characters to produce a key. Insert the string into
the bucket keyed by that key.

## Complexity
- **Time:** O(n · k log k) — n strings of average length k, each sorted in
  O(k log k).
- **Space:** O(n · k) — the buckets store all strings.

### Faster key (count-tuple)
A common optimization is to use the **character-count tuple** as the key,
e.g. `(2, 0, 0, ..., 1)` for `"aac...d"`. This drops the sort to O(k).

## Follow-ups
- *Streaming input?* Group as they come in; you don't need the full list.
- *Memory-constrained?* Sort each string in place to produce the key, but
  you'll need to keep the original. Hash a signature like `MD5(sorted)`.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

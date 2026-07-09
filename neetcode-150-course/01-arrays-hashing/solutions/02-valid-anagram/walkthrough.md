# Valid Anagram - walkthrough

**Difficulty:** Easy &middot; **Module:** 01 Arrays Hashing

## Brief

Given two strings `s` and `t`, return `True` iff `t` is an anagram of `s` (same characters, same multiplicities).

## Examples

- `s = 'anagram', t = 'nagaram'` &rarr; `True`
- `s = 'rat', t = 'car'` &rarr; `False`

## Constraints

- 1 <= len(s), len(t) <= 5 * 10^4
- Strings consist of lowercase English letters

## Intuition

Anagrams have identical character counts, so we just compare counts.

## Approach
Two equivalent options:
1. **Sort both strings** and compare — O(n log n), O(1) extra.
2. **Count** characters in a fixed-size array (`int[26]` for lowercase
   letters) — O(n), O(1) extra.

We use the count version. We don't even need a separate `int[26]` for `t`:
increment for `s`, decrement for `t`, then check that all buckets are 0.

## Complexity
- **Time:** O(n) — one pass over both strings.
- **Space:** O(1) — the count array has size 26 regardless of input.

## Follow-ups
- *Unicode input?* `int[26]` no longer works. Use a `Map<Character,Integer>`.
- *Very long strings?* Both algorithms are linear-ish; consider memory-mapping
  the file. (Outside the scope of interviews.)
- *Streaming input?* Maintain the running count and emit "still an anagram so
  far" as long as no count goes negative.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

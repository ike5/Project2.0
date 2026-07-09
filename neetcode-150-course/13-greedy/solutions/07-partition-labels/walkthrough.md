# Partition Labels - walkthrough

**Difficulty:** Medium &middot; **Module:** 13 Greedy

## Brief

You are given a string `s`. We want to partition the string into as many parts as possible so that each letter appears in at most one part. Note that the partition is done in order — a partition is valid if and only if no letter appears in more than one part. Return a list of integers representing the size of these parts.

## Examples

- `s = 'ababcbacadefegdehijhklij'` &rarr; `[9, 7, 8]`
- `s = 'eccbbbbdec'` &rarr; `[10]`

## Constraints

- 1 <= len(s) <= 500
- s consists of lowercase English letters

## Intuition

Precompute last occurrence. As we walk the string, the current
partition's end is the max of `last[c]` for chars seen. When `i ==
end`, we close the partition.

**Time:** O(n). **Space:** O(1) (26-letter alphabet).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

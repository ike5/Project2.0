# Partition Labels

**Difficulty:** Medium

## Problem

You are given a string `s`. We want to partition the string into as many parts as possible so that each letter appears in at most one part. Note that the partition is done in order — a partition is valid if and only if no letter appears in more than one part. Return a list of integers representing the size of these parts.

## Examples

```
Input:  s = 'ababcbacadefegdehijhklij'
Output: [9, 7, 8]
```

```
Input:  s = 'eccbbbbdec'
Output: [10]
```

## Constraints

- 1 <= len(s) <= 500
- s consists of lowercase English letters

## Hints

1. Precompute the last occurrence of each character. Greedily extend the current partition until it includes the last occurrence of every char seen so far.

## Solution

See [`../../solutions/07-partition-labels/`](../../solutions/07-partition-labels/) for the Python and Java 21 solutions and a step-by-step walkthrough.

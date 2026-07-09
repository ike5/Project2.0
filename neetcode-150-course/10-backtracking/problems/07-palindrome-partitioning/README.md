# Palindrome Partitioning

**Difficulty:** Medium

## Problem

Given a string `s`, partition `s` such that every substring of the partition is a palindrome. Return all possible palindrome partitionings of `s`.

## Examples

```
Input:  s = 'aab'
Output: [['a','a','b'],['aa','b']]
```

```
Input:  s = 'a'
Output: [['a']]
```

## Constraints

- 1 <= len(s) <= 16
- s contains only lowercase English letters

## Hints

1. Precompute palindrome table with DP. Backtrack by trying all partitions.

## Solution

See [`../../solutions/07-palindrome-partitioning/`](../../solutions/07-palindrome-partitioning/) for the Python and Java 21 solutions and a step-by-step walkthrough.

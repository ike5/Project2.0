# Permutation in String

**Difficulty:** Medium

## Problem

Given two strings `s1` and `s2`, return `True` if `s2` contains a permutation of `s1`. In other words, return `True` if one of `s1`'s permutations is a substring of `s2`.

## Examples

```
Input:  s1 = 'ab', s2 = 'eidbaooo'
Output: True
```

```
Input:  s1 = 'ab', s2 = 'eidboaoo'
Output: False
```

## Constraints

- 1 <= len(s1), len(s2) <= 10^4
- Strings consist of lowercase English letters

## Hints

1. Sliding window of size `len(s1)`. Compare character counts.
2. Two arrays of size 26 — compare in O(26) per slide.

## Solution

See [`../../solutions/04-permutation-in-string/`](../../solutions/04-permutation-in-string/) for the Python and Java 21 solutions and a step-by-step walkthrough.

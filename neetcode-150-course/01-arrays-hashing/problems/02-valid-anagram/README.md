# Valid Anagram

**Difficulty:** Easy

## Problem

Given two strings `s` and `t`, return `True` iff `t` is an anagram of `s` (same characters, same multiplicities).

## Examples

```
Input:  s = 'anagram', t = 'nagaram'
Output: True
```

```
Input:  s = 'rat', t = 'car'
Output: False
```

## Constraints

- 1 <= len(s), len(t) <= 5 * 10^4
- Strings consist of lowercase English letters

## Hints

1. Two strings are anagrams iff they have the same character counts.
2. `collections.Counter` does the work in one line. In Java, an `int[26]` is fastest.

## Solution

See [`../../solutions/02-valid-anagram/`](../../solutions/02-valid-anagram/) for the Python and Java 21 solutions and a step-by-step walkthrough.

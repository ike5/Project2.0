# Interleaving String

**Difficulty:** Medium

## Problem

Given strings `s1`, `s2`, and `s3`, find whether `s3` is formed by an interleaving of `s1` and `s2`. An interleaving of two strings `s` and `t` is a configuration where `s` and `t` are divided into non-empty substrings respectively, and the resulting string is `s` and `t` concatenated.

## Examples

```
Input:  s1 = 'aabcc', s2 = 'dbbca', s3 = 'aadbbcbcac'
Output: True
```

```
Input:  s1 = 'aabcc', s2 = 'dbbca', s3 = 'aadbbbaccc'
Output: False
```

## Constraints

- 0 <= len(s1), len(s2) <= 100
- 0 <= len(s3) <= 200
- s1, s2, s3 consist of lowercase English letters

## Hints

1. `dp[i][j]` = can `s3[:i+j]` be formed by interleaving `s1[:i]` and `s2[:j]`.

## Solution

See [`../../solutions/18-interleaving-string/`](../../solutions/18-interleaving-string/) for the Python and Java 21 solutions and a step-by-step walkthrough.

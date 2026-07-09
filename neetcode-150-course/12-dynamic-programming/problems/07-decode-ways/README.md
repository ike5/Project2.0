# Decode Ways

**Difficulty:** Medium

## Problem

You have intercepted a secret message encoded as a string of digits 0-9 representing letters A-Z (1=A, ..., 26=Z). Return the number of ways to decode it.

## Examples

```
Input:  s = '12'
Output: 2
```

```
Input:  s = '226'
Output: 3
```

```
Input:  s = '06'
Output: 0
```

## Constraints

- 1 <= len(s) <= 100
- s contains only digits

## Hints

1. `dp[i] = number of ways to decode s[:i]`. `dp[i] = dp[i-1]` if `s[i-1]` is non-zero; `dp[i] += dp[i-2]` if `s[i-2:i]` is in [10, 26].

## Solution

See [`../../solutions/07-decode-ways/`](../../solutions/07-decode-ways/) for the Python and Java 21 solutions and a step-by-step walkthrough.

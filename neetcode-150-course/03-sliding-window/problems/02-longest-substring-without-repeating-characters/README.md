# Longest Substring Without Repeating Characters

**Difficulty:** Medium

## Problem

Given a string `s`, find the length of the longest substring without repeating characters.

## Examples

```
Input:  s = 'abcabcbb'
Output: 3
```

```
Input:  s = 'bbbbb'
Output: 1
```

```
Input:  s = 'pwwkew'
Output: 3
```

## Constraints

- 0 <= len(s) <= 5 * 10^4
- s consists of English letters, digits, symbols, and spaces

## Hints

1. Sliding window: maintain `[l, r)` with no repeats.
2. Use a `set` / `int[128]` to track which chars are in the window. When `s[r]` is already in the set, advance `l` until it isn't.

## Solution

See [`../../solutions/02-longest-substring-without-repeating-characters/`](../../solutions/02-longest-substring-without-repeating-characters/) for the Python and Java 21 solutions and a step-by-step walkthrough.

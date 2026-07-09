# Longest Repeating Character Replacement

**Difficulty:** Medium

## Problem

You are given a string `s` and an integer `k`. You can choose any character of the string and change it to any other uppercase English character. You can perform this operation at most `k` times. Return the length of the longest substring containing the same letter you can get after performing the above operations.

## Examples

```
Input:  s = 'ABAB', k = 2
Output: 4
```

```
Input:  s = 'AABABBA', k = 1
Output: 4
```

## Constraints

- 1 <= len(s) <= 10^5
- 0 <= k <= len(s)
- s consists of only uppercase English letters

## Hints

1. For a window, the number of replacements needed is `window_length - max_count_in_window`.
2. If that exceeds `k`, shrink from the left.

## Solution

See [`../../solutions/03-longest-repeating-character-replacement/`](../../solutions/03-longest-repeating-character-replacement/) for the Python and Java 21 solutions and a step-by-step walkthrough.

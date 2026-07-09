# Palindromic Substrings

**Difficulty:** Medium

## Problem

Given a string `s`, return the number of palindromic substrings in it. A string is a palindrome when it reads the same backward as forward. A substring is a contiguous sequence of characters in the string.

## Examples

```
Input:  s = 'abc'
Output: 3
```

```
Input:  s = 'aaa'
Output: 6
```

## Constraints

- 1 <= len(s) <= 1000
- s consists of lowercase English letters

## Hints

1. Same expand-around-center technique. Count instead of tracking the longest.

## Solution

See [`../../solutions/06-palindromic-substrings/`](../../solutions/06-palindromic-substrings/) for the Python and Java 21 solutions and a step-by-step walkthrough.

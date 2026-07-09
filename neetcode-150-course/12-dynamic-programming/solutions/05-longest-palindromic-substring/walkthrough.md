# Longest Palindromic Substring - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

Given a string `s`, return the longest palindromic substring.

## Examples

- `s = 'babad'` &rarr; `'bab' or 'aba'`
- `s = 'cbbd'` &rarr; `'bb'`

## Constraints

- 1 <= len(s) <= 1000
- s consist of only digits and English letters

## Intuition

Expand around each possible center. A palindrome's center can be
on a character (odd length) or between two (even length).

**Time:** O(n²). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

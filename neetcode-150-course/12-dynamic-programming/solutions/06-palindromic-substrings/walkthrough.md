# Palindromic Substrings - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

Given a string `s`, return the number of palindromic substrings in it. A string is a palindrome when it reads the same backward as forward. A substring is a contiguous sequence of characters in the string.

## Examples

- `s = 'abc'` &rarr; `3`
- `s = 'aaa'` &rarr; `6`

## Constraints

- 1 <= len(s) <= 1000
- s consists of lowercase English letters

## Intuition

Same expand-around-center. Count each palindrome as we expand.

**Time:** O(n²). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

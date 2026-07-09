# Valid Palindrome - walkthrough

**Difficulty:** Easy &middot; **Module:** 02 Two Pointers

## Brief

Given a string `s`, return `True` if it is a palindrome after converting all uppercase letters to lowercase and removing all non-alphanumeric characters.

## Examples

- `s = 'A man, a plan, a canal: Panama'` &rarr; `True`
- `s = 'race a car'` &rarr; `False`
- `s = ' '` &rarr; `True`

## Constraints

- 1 <= len(s) <= 2 * 10^5
- s consists of printable ASCII characters

## Intuition

Two pointers from opposite ends. Skip non-alphanumeric characters at
each step. Compare the lowercased chars. If they ever differ, the string is
not a palindrome.

**Time:** O(n). **Space:** O(1) — pointers only.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

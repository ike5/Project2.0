# Valid Parentheses - walkthrough

**Difficulty:** Easy &middot; **Module:** 04 Stack

## Brief

Given a string `s` containing just the characters '()[]{}', determine if the input string is valid. Brackets must be closed in the correct order, and every open bracket must be matched by a close bracket of the same type.

## Examples

- `s = '()[]{}'` &rarr; `True`
- `s = '(]'` &rarr; `False`
- `s = '([)]'` &rarr; `False`
- `s = '{[]}'` &rarr; `True`

## Constraints

- 1 <= len(s) <= 10^4
- s consists of parentheses only

## Intuition

Push openers. On a closer, the stack top must be the matching opener
(else invalid). At the end, the stack must be empty.

**Time:** O(n). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

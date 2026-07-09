# Valid Parenthesis String - walkthrough

**Difficulty:** Medium &middot; **Module:** 13 Greedy

## Brief

Given a string `s` containing only three types of characters: '(', ')', and '*', return `True` if `s` is **valid**. The rules: (1) any left parenthesis `'('` must have a corresponding right parenthesis `')'`. (2) any right parenthesis `')'` must have a corresponding left parenthesis `'('`. (3) left parenthesis `'('` must go before the corresponding right parenthesis `')'`. (4) `*` could be treated as a single right parenthesis `')'` or a single left parenthesis `'('` or an empty string.

## Examples

- `s = '()'` &rarr; `True`
- `s = '(*)'` &rarr; `True`
- `s = '(*))'` &rarr; `True`

## Constraints

- 1 <= len(s) <= 100
- s consists of '(' , ')' and '*'

## Intuition

Track a range `[lo, hi]` of possible open counts after each
char. `(` adds 1, `)` removes 1 (clamped at 0), `*` is either. At the
end we need `lo == 0`.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

# Evaluate Reverse Polish Notation - walkthrough

**Difficulty:** Medium &middot; **Module:** 04 Stack

## Brief

Evaluate the value of an arithmetic expression in Reverse Polish Notation. Valid operators are `+`, `-`, `*`, `/`. Each operand may be an integer or another expression. Division between two integers should **truncate toward zero**.

## Examples

- `tokens = ['2','1','+','3','*']` &rarr; `9`
- `tokens = ['4','13','5','/','+']` &rarr; `6`
- `tokens = ['10','6','9','3','+','-11','*','/','*','17','+','5','+']` &rarr; `22`

## Constraints

- 1 <= len(tokens) <= 10^4
- tokens[i] is either an integer in [-200, 200] or one of '+-*/'
- The expression is always valid and divides by zero never occurs

## Intuition

Stack-based. Numbers push. Operators pop the top two, compute, push
the result. Watch the order: for `a - b` and `a / b`, the second-popped is
`b`. In Java, `int / int` already truncates toward zero, so no special
handling. In Python, `int(a / b)` (not `a // b`) is required to match
the problem's contract for negative results.

**Time:** O(n). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

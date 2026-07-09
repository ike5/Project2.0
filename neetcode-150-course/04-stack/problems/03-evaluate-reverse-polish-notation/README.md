# Evaluate Reverse Polish Notation

**Difficulty:** Medium

## Problem

Evaluate the value of an arithmetic expression in Reverse Polish Notation. Valid operators are `+`, `-`, `*`, `/`. Each operand may be an integer or another expression. Division between two integers should **truncate toward zero**.

## Examples

```
Input:  tokens = ['2','1','+','3','*']
Output: 9
```

```
Input:  tokens = ['4','13','5','/','+']
Output: 6
```

```
Input:  tokens = ['10','6','9','3','+','-11','*','/','*','17','+','5','+']
Output: 22
```

## Constraints

- 1 <= len(tokens) <= 10^4
- tokens[i] is either an integer in [-200, 200] or one of '+-*/'
- The expression is always valid and divides by zero never occurs

## Hints

1. Push numbers; on an operator, pop two, compute, push the result.
2. Order matters: for `a - b` and `a / b`, the first popped is `b`.

## Solution

See [`../../solutions/03-evaluate-reverse-polish-notation/`](../../solutions/03-evaluate-reverse-polish-notation/) for the Python and Java 21 solutions and a step-by-step walkthrough.

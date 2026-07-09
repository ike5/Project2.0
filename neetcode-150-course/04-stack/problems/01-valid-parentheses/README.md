# Valid Parentheses

**Difficulty:** Easy

## Problem

Given a string `s` containing just the characters '()[]{}', determine if the input string is valid. Brackets must be closed in the correct order, and every open bracket must be matched by a close bracket of the same type.

## Examples

```
Input:  s = '()[]{}'
Output: True
```

```
Input:  s = '(]'
Output: False
```

```
Input:  s = '([)]'
Output: False
```

```
Input:  s = '{[]}'
Output: True
```

## Constraints

- 1 <= len(s) <= 10^4
- s consists of parentheses only

## Hints

1. Push opening brackets; on a closing bracket, the top of the stack must be the matching opener.
2. At the end the stack must be empty.

## Solution

See [`../../solutions/01-valid-parentheses/`](../../solutions/01-valid-parentheses/) for the Python and Java 21 solutions and a step-by-step walkthrough.

# Valid Parenthesis String

**Difficulty:** Medium

## Problem

Given a string `s` containing only three types of characters: '(', ')', and '*', return `True` if `s` is **valid**. The rules: (1) any left parenthesis `'('` must have a corresponding right parenthesis `')'`. (2) any right parenthesis `')'` must have a corresponding left parenthesis `'('`. (3) left parenthesis `'('` must go before the corresponding right parenthesis `')'`. (4) `*` could be treated as a single right parenthesis `')'` or a single left parenthesis `'('` or an empty string.

## Examples

```
Input:  s = '()'
Output: True
```

```
Input:  s = '(*)'
Output: True
```

```
Input:  s = '(*))'
Output: True
```

## Constraints

- 1 <= len(s) <= 100
- s consists of '(' , ')' and '*'

## Hints

1. Greedy: track the range of possible open counts. `*` can be `(`, `)`, or empty.

## Solution

See [`../../solutions/08-valid-parenthesis-string/`](../../solutions/08-valid-parenthesis-string/) for the Python and Java 21 solutions and a step-by-step walkthrough.

# Copy List With Random Pointer

**Difficulty:** Medium

## Problem

Construct a deep copy of a linked list where each node has an additional `random` pointer that could point to any node in the list or null. Return the head of the deep copy.

## Examples

```
Input:  head = [[7,null],[13,0],[11,4],[10,2],[1,0]]
Output: [[7,null],[13,0],[11,4],[10,2],[1,0]]
```

## Constraints

- 0 <= n <= 1000
- -10^4 <= Node.val <= 10^4

## Hints

1. Three-pass: (1) interleave clones with originals; (2) wire up `random`; (3) split into two lists.
2. Or: a `dict[old, new]` and a second pass.

## Solution

See [`../../solutions/05-copy-list-with-random-pointer/`](../../solutions/05-copy-list-with-random-pointer/) for the Python and Java 21 solutions and a step-by-step walkthrough.

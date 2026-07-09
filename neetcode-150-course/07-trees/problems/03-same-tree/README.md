# Same Tree

**Difficulty:** Easy

## Problem

Given the roots of two binary trees `p` and `q`, write a function to check if they are the same or not. Two binary trees are considered the same if they are structurally identical, and the nodes have the same value.

## Examples

```
Input:  p = [1,2,3], q = [1,2,3]
Output: True
```

```
Input:  p = [1,2], q = [1,null,2]
Output: False
```

## Constraints

- 0 <= number of nodes <= 100
- -10^4 <= Node.val <= 10^4

## Hints

1. Recursive: both null → true; one null → false; compare values and recurse on both children.

## Solution

See [`../../solutions/03-same-tree/`](../../solutions/03-same-tree/) for the Python and Java 21 solutions and a step-by-step walkthrough.

# Kth Smallest Element in a BST

**Difficulty:** Medium

## Problem

Given the `root` of a binary search tree, and an integer `k`, return the `k`th smallest value (1-indexed) of all the values of the nodes in the tree.

## Examples

```
Input:  root = [3,1,4,null,2], k = 1
Output: 1
```

```
Input:  root = [5,3,6,2,4,null,null,1], k = 3
Output: 3
```

## Constraints

- 1 <= k <= number of nodes <= 10^4
- 0 <= Node.val <= 10^4

## Hints

1. In-order traversal of a BST yields sorted values; stop at the kth.
2. Or, augmented BST with subtree sizes for O(h) queries (not in this course).

## Solution

See [`../../solutions/06-kth-smallest-element-in-a-bst/`](../../solutions/06-kth-smallest-element-in-a-bst/) for the Python and Java 21 solutions and a step-by-step walkthrough.

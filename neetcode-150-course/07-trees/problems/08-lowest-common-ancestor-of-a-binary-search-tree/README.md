# Lowest Common Ancestor of a Binary Search Tree

**Difficulty:** Medium

## Problem

Given a binary search tree (BST), find the lowest common ancestor (LCA) of two given nodes in the BST. The LCA is the lowest node in T that has both p and q as descendants (a node can be a descendant of itself).

## Examples

```
Input:  root = [6,2,8,0,4,7,9,null,null,3,5], p = 2, q = 8
Output: 6
```

```
Input:  root = [6,2,8,0,4,7,9,null,null,3,5], p = 2, q = 4
Output: 2
```

## Constraints

- 2 <= number of nodes <= 10^5
- -10^9 <= Node.val <= 10^9
- All Node.val are unique
- p != q
- p and q exist in the BST

## Hints

1. Walk from the root. If both p and q are smaller, go left; if both larger, go right; otherwise, current is the LCA.

## Solution

See [`../../solutions/08-lowest-common-ancestor-of-a-binary-search-tree/`](../../solutions/08-lowest-common-ancestor-of-a-binary-search-tree/) for the Python and Java 21 solutions and a step-by-step walkthrough.

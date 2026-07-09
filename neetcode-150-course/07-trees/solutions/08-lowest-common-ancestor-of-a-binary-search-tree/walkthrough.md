# Lowest Common Ancestor of a Binary Search Tree - walkthrough

**Difficulty:** Medium &middot; **Module:** 07 Trees

## Brief

Given a binary search tree (BST), find the lowest common ancestor (LCA) of two given nodes in the BST. The LCA is the lowest node in T that has both p and q as descendants (a node can be a descendant of itself).

## Examples

- `root = [6,2,8,0,4,7,9,null,null,3,5], p = 2, q = 8` &rarr; `6`
- `root = [6,2,8,0,4,7,9,null,null,3,5], p = 2, q = 4` &rarr; `2`

## Constraints

- 2 <= number of nodes <= 10^5
- -10^9 <= Node.val <= 10^9
- All Node.val are unique
- p != q
- p and q exist in the BST

## Intuition

Because it's a BST, the LCA is the first node whose value is
**between** p and q. Walk from the root, branching left or right until
the current node splits them.

**Time:** O(h). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

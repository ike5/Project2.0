# Kth Smallest Element in a BST - walkthrough

**Difficulty:** Medium &middot; **Module:** 07 Trees

## Brief

Given the `root` of a binary search tree, and an integer `k`, return the `k`th smallest value (1-indexed) of all the values of the nodes in the tree.

## Examples

- `root = [3,1,4,null,2], k = 1` &rarr; `1`
- `root = [5,3,6,2,4,null,null,1], k = 3` &rarr; `3`

## Constraints

- 1 <= k <= number of nodes <= 10^4
- 0 <= Node.val <= 10^4

## Intuition

Iterative in-order traversal. Stop when we've seen `k` nodes.

**Time:** O(h + k). **Space:** O(h).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

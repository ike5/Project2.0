# Count Good Nodes in Binary Tree - walkthrough

**Difficulty:** Medium &middot; **Module:** 07 Trees

## Brief

Given a binary tree `root`, a node `x` in the tree is named **good** if in the path from root to `x`, there are no nodes with a value greater than `x`'s. Return the number of good nodes in the binary tree.

## Examples

- `root = [3,1,4,3,null,1,5]` &rarr; `4`
- `root = [3,3,null,4,2]` &rarr; `3`

## Constraints

- 1 <= number of nodes <= 10^5
- -10^4 <= Node.val <= 10^4

## Intuition

DFS with a `max_so_far` parameter. The root is always good.

**Time:** O(n). **Space:** O(h).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

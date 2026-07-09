# Binary Tree Maximum Path Sum - walkthrough

**Difficulty:** Hard &middot; **Module:** 07 Trees

## Brief

A **path** in a binary tree is a sequence of nodes where each pair of adjacent nodes in the sequence has an edge connecting them. A node can only appear in the sequence at most once. Note that the path does not need to pass through the root. The **path sum** of a path is the sum of the node's values in the path. Given the `root` of a binary tree, return the maximum path sum of any **non-empty** path.

## Examples

- `root = [1,2,3]` &rarr; `6`
- `root = [-10,9,20,null,null,15,7]` &rarr; `42`

## Constraints

- 1 <= number of nodes <= 3 * 10^4
- -1000 <= Node.val <= 1000

## Intuition

For each node, the best path **through it** is
`node.val + max(0, left_gain) + max(0, right_gain)`. The best
**single-branch** path going up is `node.val + max(0, max(left_gain,
right_gain))`.

**Time:** O(n). **Space:** O(h).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

# Maximum Depth of Binary Tree - walkthrough

**Difficulty:** Easy &middot; **Module:** 07 Trees

## Brief

Given the `root` of a binary tree, return its maximum depth. A binary tree's maximum depth is the number of nodes along the longest path from the root node down to the farthest leaf node.

## Examples

- `root = [3,9,20,null,null,15,7]` &rarr; `3`
- `root = [1,null,2]` &rarr; `2`

## Constraints

- 0 <= number of nodes <= 10^4
- -100 <= Node.val <= 100

## Intuition

Recursive: 1 + max of children's depths.

**Time:** O(n). **Space:** O(h) recursion.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

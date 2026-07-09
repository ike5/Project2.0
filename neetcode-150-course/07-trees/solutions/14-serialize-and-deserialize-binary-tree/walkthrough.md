# Serialize and Deserialize Binary Tree - walkthrough

**Difficulty:** Hard &middot; **Module:** 07 Trees

## Brief

Serialization is the process of converting a data structure or object into a sequence of bits so that it can be stored in a file or memory buffer, or transmitted across a network connection link to be reconstructed later in the same or another computer environment. Design an algorithm to serialize and deserialize a binary tree.

## Examples

- `root = [1,2,3,null,null,4,5]` &rarr; `1,2,None,None,3,4,None,None,5,None,None`

## Constraints

- 0 <= number of nodes <= 10^4
- -1000 <= Node.val <= 1000

## Intuition

**Preorder DFS** is the simplest format. Serialize writes `val` or
`null` for each visit. Deserialize uses a queue of tokens.

**Time:** O(n). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

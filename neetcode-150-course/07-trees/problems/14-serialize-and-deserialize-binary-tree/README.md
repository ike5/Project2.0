# Serialize and Deserialize Binary Tree

**Difficulty:** Hard

## Problem

Serialization is the process of converting a data structure or object into a sequence of bits so that it can be stored in a file or memory buffer, or transmitted across a network connection link to be reconstructed later in the same or another computer environment. Design an algorithm to serialize and deserialize a binary tree.

## Examples

```
Input:  root = [1,2,3,null,null,4,5]
Output: 1,2,None,None,3,4,None,None,5,None,None
```

## Constraints

- 0 <= number of nodes <= 10^4
- -1000 <= Node.val <= 1000

## Hints

1. Preorder DFS. Serialize: 'val,null,null,...' for missing children.
2. Deserialize: read tokens; null consumes nothing, value creates a node and recurses on left and right.

## Solution

See [`../../solutions/14-serialize-and-deserialize-binary-tree/`](../../solutions/14-serialize-and-deserialize-binary-tree/) for the Python and Java 21 solutions and a step-by-step walkthrough.

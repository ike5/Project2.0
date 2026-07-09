# Construct Binary Tree from Preorder and Inorder Traversal

**Difficulty:** Medium

## Problem

Given two integer arrays `preorder` and `inorder` where `preorder` is the preorder traversal of a binary tree and `inorder` is the inorder traversal of the same tree, construct and return the binary tree.

## Examples

```
Input:  preorder = [3,9,20,15,7], inorder = [9,3,15,20,7]
Output: [3,9,20,null,null,15,7]
```

## Constraints

- 1 <= len(preorder) == len(inorder) <= 3000
- -3000 <= preorder[i], inorder[i] <= 3000
- All values are unique

## Hints

1. Preorder's first element is the root. In inorder, the root splits left and right subtrees.
2. Recurse on the two halves. Use a hash map for O(1) lookups in inorder.

## Solution

See [`../../solutions/09-construct-binary-tree-from-preorder-and-inorder-traversal/`](../../solutions/09-construct-binary-tree-from-preorder-and-inorder-traversal/) for the Python and Java 21 solutions and a step-by-step walkthrough.

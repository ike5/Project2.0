# Construct Binary Tree from Preorder and Inorder Traversal - walkthrough

**Difficulty:** Medium &middot; **Module:** 07 Trees

## Brief

Given two integer arrays `preorder` and `inorder` where `preorder` is the preorder traversal of a binary tree and `inorder` is the inorder traversal of the same tree, construct and return the binary tree.

## Examples

- `preorder = [3,9,20,15,7], inorder = [9,3,15,20,7]` &rarr; `[3,9,20,null,null,15,7]`

## Constraints

- 1 <= len(preorder) == len(inorder) <= 3000
- -3000 <= preorder[i], inorder[i] <= 3000
- All values are unique

## Intuition

Preorder gives us the root (first element). In inorder, the root
splits the array into left and right subtree elements. Recurse on each
half.

A `dict[value, index]` over inorder gives O(1) lookups, making the
overall algorithm O(n).

**Time:** O(n). **Space:** O(n) for the map and recursion.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

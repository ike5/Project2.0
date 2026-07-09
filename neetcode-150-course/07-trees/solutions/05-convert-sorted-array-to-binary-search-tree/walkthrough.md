# Convert Sorted Array to Binary Search Tree - walkthrough

**Difficulty:** Easy &middot; **Module:** 07 Trees

## Brief

Given an integer array `nums` where the elements are sorted in **ascending** order, convert it to a height-balanced binary search tree. A height-balanced tree is one in which the depths of the two subtrees of every node never differ by more than 1.

## Examples

- `nums = [-10,-3,0,5,9]` &rarr; `[0,-3,9,-10,null,5]`
- `nums = [1,3]` &rarr; `[3,1]`

## Constraints

- 1 <= len(nums) <= 10^4
- -10^4 <= nums[i] <= 10^4
- nums is sorted in strictly increasing order

## Intuition

Pick the middle as root, recurse on left and right halves. Picking
the *exact* middle keeps the tree balanced.

**Time:** O(n). **Space:** O(h) for the recursion; O(n) total nodes.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

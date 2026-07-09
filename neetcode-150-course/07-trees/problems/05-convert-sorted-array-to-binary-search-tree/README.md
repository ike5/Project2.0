# Convert Sorted Array to Binary Search Tree

**Difficulty:** Easy

## Problem

Given an integer array `nums` where the elements are sorted in **ascending** order, convert it to a height-balanced binary search tree. A height-balanced tree is one in which the depths of the two subtrees of every node never differ by more than 1.

## Examples

```
Input:  nums = [-10,-3,0,5,9]
Output: [0,-3,9,-10,null,5]
```

```
Input:  nums = [1,3]
Output: [3,1]
```

## Constraints

- 1 <= len(nums) <= 10^4
- -10^4 <= nums[i] <= 10^4
- nums is sorted in strictly increasing order

## Hints

1. Recurse: pick the middle as root, recurse on left and right halves.

## Solution

See [`../../solutions/05-convert-sorted-array-to-binary-search-tree/`](../../solutions/05-convert-sorted-array-to-binary-search-tree/) for the Python and Java 21 solutions and a step-by-step walkthrough.

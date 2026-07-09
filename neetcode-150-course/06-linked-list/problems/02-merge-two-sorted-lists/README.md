# Merge Two Sorted Lists

**Difficulty:** Easy

## Problem

You are given the heads of two sorted linked lists `list1` and `list2`. Merge the two lists into one **sorted** list and return its head. The list should be made by splicing together the nodes of the first two lists.

## Examples

```
Input:  list1 = [1,2,4], list2 = [1,3,4]
Output: [1,1,2,3,4,4]
```

```
Input:  list1 = [], list2 = []
Output: []
```

```
Input:  list1 = [], list2 = [0]
Output: [0]
```

## Constraints

- 0 <= number of nodes in each list <= 50
- -100 <= Node.val <= 100
- Both lists are sorted in non-decreasing order

## Hints

1. Use a dummy head and a tail pointer; pick the smaller front each step.

## Solution

See [`../../solutions/02-merge-two-sorted-lists/`](../../solutions/02-merge-two-sorted-lists/) for the Python and Java 21 solutions and a step-by-step walkthrough.

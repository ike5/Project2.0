# Reverse Nodes in k-Group

**Difficulty:** Hard

## Problem

Given the `head` of a linked list, reverse the nodes of the list `k` at a time, and return the modified list. `k` is a positive integer. If the number of nodes is not a multiple of `k`, the remaining nodes at the end should stay in the same order.

## Examples

```
Input:  head = [1,2,3,4,5], k = 2
Output: [2,1,4,3,5]
```

```
Input:  head = [1,2,3,4,5], k = 3
Output: [3,2,1,4,5]
```

## Constraints

- 1 <= k <= number of nodes
- 0 <= number of nodes <= 5000
- 0 <= Node.val <= 1000

## Hints

1. Check that k nodes remain; if so, reverse them; otherwise, leave.
2. Use a helper that reverses the next k nodes and returns the new head.

## Solution

See [`../../solutions/11-reverse-nodes-in-k-group/`](../../solutions/11-reverse-nodes-in-k-group/) for the Python and Java 21 solutions and a step-by-step walkthrough.

# Merge K Sorted Lists

**Difficulty:** Hard

## Problem

You are given an array of `k` linked lists, each sorted in ascending order. Merge all the linked lists into one sorted linked list and return it.

## Examples

```
Input:  lists = [[1,4,5],[1,3,4],[2,6]]
Output: [1,1,2,3,4,4,5,6]
```

```
Input:  lists = []
Output: []
```

```
Input:  lists = [[]]
Output: []
```

## Constraints

- 0 <= k <= 10^4
- 0 <= lists[i].length <= 500
- -10^4 <= lists[i][j] <= 10^4
- lists[i] is sorted in ascending order
- The total number of nodes won't exceed 10^4

## Hints

1. Min-heap of size k, popping the smallest head each step.
2. Or divide-and-conquer: pair-merge, then merge the pairs, etc.

## Solution

See [`../../solutions/10-merge-k-sorted-lists/`](../../solutions/10-merge-k-sorted-lists/) for the Python and Java 21 solutions and a step-by-step walkthrough.

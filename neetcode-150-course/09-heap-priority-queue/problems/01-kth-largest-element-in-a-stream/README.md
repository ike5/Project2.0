# Kth Largest Element in a Stream

**Difficulty:** Easy

## Problem

Design a class to find the kth largest element in a stream. Note that it is the kth largest element in the sorted order, not the kth distinct element. Implement `KthLargest` with `add(val)`.

## Examples

```
Input:  KthLargest(3, [4, 5, 8, 2]); add(3) -> 4; add(5) -> 5; add(10) -> 5; add(9) -> 8; add(4) -> 8
Output: 4, 5, 5, 8, 8
```

## Constraints

- 1 <= k <= 10^4
- 0 <= len(nums) <= 10^4
- -10^4 <= val <= 10^4
- At most 10^4 calls to add

## Hints

1. Min-heap of size k. The top is the kth largest.

## Solution

See [`../../solutions/01-kth-largest-element-in-a-stream/`](../../solutions/01-kth-largest-element-in-a-stream/) for the Python and Java 21 solutions and a step-by-step walkthrough.

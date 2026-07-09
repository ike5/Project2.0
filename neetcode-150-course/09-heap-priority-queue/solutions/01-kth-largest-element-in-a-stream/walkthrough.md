# Kth Largest Element in a Stream - walkthrough

**Difficulty:** Easy &middot; **Module:** 09 Heap Priority Queue

## Brief

Design a class to find the kth largest element in a stream. Note that it is the kth largest element in the sorted order, not the kth distinct element. Implement `KthLargest` with `add(val)`.

## Examples

- `KthLargest(3, [4, 5, 8, 2]); add(3) -> 4; add(5) -> 5; add(10) -> 5; add(9) -> 8; add(4) -> 8` &rarr; `4, 5, 5, 8, 8`

## Constraints

- 1 <= k <= 10^4
- 0 <= len(nums) <= 10^4
- -10^4 <= val <= 10^4
- At most 10^4 calls to add

## Intuition

A **min-heap of size k** holds the k largest values seen so far.
The smallest of those is the kth largest overall. Insert and trim to
size k after each `add`.

**Time:** O(log k) per add. **Space:** O(k).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

# Find Median from Data Stream - walkthrough

**Difficulty:** Hard &middot; **Module:** 09 Heap Priority Queue

## Brief

The **median** is the middle value in an ordered integer list. If the size of the list is even, there is no middle value, and the median is the mean of the two middle values. Implement the `MedianFinder` class: `add_num(int)` and `find_median() -> float`.

## Examples

- `MedianFinder(); addNum(1); addNum(2); findMedian() -> 1.5; addNum(3); findMedian() -> 2.0` &rarr; `1.5, 2.0`

## Constraints

- -10^5 <= num <= 10^5
- At most 5 * 10^4 calls to addNum and findMedian
- At least one call to findMedian after addNum

## Intuition

Two heaps:
- **max-heap `small`** holds the lower half.
- **min-heap `large`** holds the upper half.

After each `addNum`, rebalance so that `|len(small) - len(large)| <= 1`.

The median is `small.top` (if `small` is bigger) or the average of
`small.top` and `large.top`.

**Time:** O(log n) per addNum, O(1) per findMedian.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

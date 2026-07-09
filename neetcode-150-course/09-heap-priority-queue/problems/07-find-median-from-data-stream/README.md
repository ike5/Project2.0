# Find Median from Data Stream

**Difficulty:** Hard

## Problem

The **median** is the middle value in an ordered integer list. If the size of the list is even, there is no middle value, and the median is the mean of the two middle values. Implement the `MedianFinder` class: `add_num(int)` and `find_median() -> float`.

## Examples

```
Input:  MedianFinder(); addNum(1); addNum(2); findMedian() -> 1.5; addNum(3); findMedian() -> 2.0
Output: 1.5, 2.0
```

## Constraints

- -10^5 <= num <= 10^5
- At most 5 * 10^4 calls to addNum and findMedian
- At least one call to findMedian after addNum

## Hints

1. Two heaps: a max-heap of the small half and a min-heap of the large half. The median is at the top of one or the average of both.

## Solution

See [`../../solutions/07-find-median-from-data-stream/`](../../solutions/07-find-median-from-data-stream/) for the Python and Java 21 solutions and a step-by-step walkthrough.

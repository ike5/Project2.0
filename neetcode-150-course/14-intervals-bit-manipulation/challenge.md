# Challenge 14 — Intervals & Bit Manipulation

## Tasks

### 1. Insert Interval
[`problems/01-insert-interval/`](./problems/01-insert-interval/)

```python
assert insert([[1, 3], [6, 9]], [2, 5]) == [[1, 5], [6, 9]]
assert insert([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]) == [[1, 2], [3, 10], [12, 16]]
```

### 2. Non-Overlapping Intervals
[`problems/03-non-overlapping-intervals/`](./problems/03-non-overlapping-intervals/)

```python
assert erase_overlap_intervals([[1,2],[2,3],[3,4],[1,3]]) == 1
assert erase_overlap_intervals([[1,2],[1,2],[1,2]]) == 2
assert erase_overlap_intervals([[1,2],[2,3]]) == 0
```

### 3. Bitwise AND of Numbers Range
[`problems/08-bitwise-and-of-numbers-range/`](./problems/08-bitwise-and-of-numbers-range/)

```python
assert range_bitwise_and(5, 7) == 4
assert range_bitwise_and(0, 0) == 0
assert range_bitwise_and(1, 2147483647) == 0
```

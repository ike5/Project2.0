# Challenge 09 — Heap

## Tasks

### 1. K Closest Points to Origin
[`problems/03-k-closest-points-to-origin/`](./problems/03-k-closest-points-to-origin/)

```python
assert sorted(k_closest([[1, 3], [-2, 2]], 2)) == [[-2, 2], [1, 3]]
assert sorted(k_closest([[3, 3], [5, -1], [-2, 4]], 2)) == [[-2, 4], [3, 3]]
```

### 2. Task Scheduler
[`problems/05-task-scheduler/`](./problems/05-task-scheduler/)

```python
assert least_interval(["A","A","A","B","B","B"], 2) == 8
assert least_interval(["A","A","A","B","B","B"], 0) == 6
```

### 3. Find Median from Data Stream (hard)
[`problems/07-find-median-from-data-stream/`](./problems/07-find-median-from-data-stream/)

```python
mf = MedianFinder()
mf.add_num(1); mf.add_num(2)
assert mf.find_median() == 1.5
mf.add_num(3)
assert mf.find_median() == 2.0
```

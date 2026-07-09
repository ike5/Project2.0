# Challenge 02 — Two Pointers

Solutions live next to each problem in `solutions/`. Try the lab first.

## Tasks

Three problems, both languages, all in O(n) or O(n log n).

### 1. 3Sum
See [`problems/03-three-sum/`](./problems/03-three-sum/).

```python
# Python
assert sorted([sorted(t) for t in three_sum([-1, 0, 1, 2, -1, -4])]) == [[-1, -1, 2], [-1, 0, 1]]
assert three_sum([0, 1, 1]) == []
assert three_sum([0, 0, 0]) == [[0, 0, 0]]
```

### 2. Container With Most Water
See [`problems/04-container-with-most-water/`](./problems/04-container-with-most-water/).

```python
assert max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49
assert max_area([1, 1]) == 1
assert max_area([4, 3, 2, 1, 4]) == 16
```

### 3. Trapping Rain Water
See [`problems/05-trapping-rain-water/`](./problems/05-trapping-rain-water/).

```python
assert trap([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) == 6
assert trap([4, 2, 0, 3, 2, 5]) == 9
```

## Success criteria

- [ ] All three Python files pass their asserts.
- [ ] All three Java files compile and print the expected values.
- [ ] Each solution is O(n) or O(n log n).

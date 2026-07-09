# Challenge 05 — Binary Search

Solutions live next to each problem in `solutions/`.

## Tasks

Three problems, both languages.

### 1. Koko Eating Bananas (search on answer)
[`problems/03-koko-eating-bananas/`](./problems/03-koko-eating-bananas/)

```python
assert min_eating_speed([1, 4, 3, 2], 9) == 2
assert min_eating_speed([25, 10, 23, 4], 4) == 25
```

### 2. Search in Rotated Sorted Array
[`problems/05-search-in-rotated-sorted-array/`](./problems/05-search-in-rotated-sorted-array/)

```python
assert search_rotated([4, 5, 6, 7, 0, 1, 2], 0) == 4
assert search_rotated([4, 5, 6, 7, 0, 1, 2], 3) == -1
```

### 3. Median of Two Sorted Arrays (hard)
[`problems/07-median-of-two-sorted-arrays/`](./problems/07-median-of-two-sorted-arrays/)

```python
import math
assert math.isclose(find_median_sorted_arrays([1, 3], [2]), 2.0)
assert math.isclose(find_median_sorted_arrays([1, 2], [3, 4]), 2.5)
```

## Success criteria

- [ ] All three Python files pass.
- [ ] All three Java files compile and print the expected values.
- [ ] Median solution runs in O(log(min(m, n))).

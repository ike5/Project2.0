# Challenge 03 — Sliding Window

Solutions live next to each problem in `solutions/`.

## Tasks

Three problems, both languages, all O(n).

### 1. Longest Repeating Character Replacement
[`problems/03-longest-repeating-character-replacement/`](./problems/03-longest-repeating-character-replacement/)

```python
assert character_replacement("ABAB", 2) == 4
assert character_replacement("AABABBA", 1) == 4
```

### 2. Minimum Size Subarray Sum
[`problems/05-minimum-size-subarray-sum/`](./problems/05-minimum-size-subarray-sum/)

```python
assert min_sub_array_len(7, [2, 3, 1, 2, 4, 3]) == 2
assert min_sub_array_len(4, [1, 4, 4]) == 1
assert min_sub_array_len(11, [1, 1, 1, 1, 1, 1, 1, 1]) == 0
```

### 3. Sliding Window Maximum (the hard one — uses a monotonic deque)
[`problems/06-sliding-window-maximum/`](./problems/06-sliding-window-maximum/)

```python
assert max_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
assert max_sliding_window([1], 1) == [1]
```

## Success criteria

- [ ] All three Python files pass.
- [ ] All three Java files compile and print the expected values.
- [ ] Each solution is O(n).

# Challenge 10 — Backtracking

## Tasks

### 1. Combination Sum
[`problems/02-combination-sum/`](./problems/02-combination-sum/)

```python
got = sorted([sorted(c) for c in combination_sum([2, 3, 6, 7], 7)])
expected = [[2, 2, 3], [7]]
assert got == sorted([sorted(c) for c in expected])
```

### 2. Word Search
[`problems/06-word-search/`](./problems/06-word-search/)

```python
b = [["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]]
assert exist(b, "ABCCED") is True
assert exist(b, "ABCB") is False
```

### 3. N-Queens (hard)
[`problems/09-n-queens/`](./problems/09-n-queens/)

```python
assert len(solve_n_queens(4)) == 2
assert len(solve_n_queens(1)) == 1
```

# Challenge 12 — Dynamic Programming

## Tasks

### 1. Coin Change
[`problems/08-coin-change/`](./problems/08-coin-change/)

```python
assert coin_change([1, 5, 10, 25], 30) == 2
assert coin_change([2], 3) == -1
```

### 2. Longest Common Subsequence
[`problems/14-longest-common-subsequence/`](./problems/14-longest-common-subsequence/)

```python
assert longest_common_subsequence("abcde", "ace") == 3
assert longest_common_subsequence("abc", "abc") == 3
assert longest_common_subsequence("abc", "def") == 0
```

### 3. Edit Distance
[`problems/19-edit-distance/`](./problems/19-edit-distance/)

```python
assert min_distance("horse", "ros") == 3
assert min_distance("intention", "execution") == 5
```

### 4. Maximal Square (hard)
[`problems/22-maximal-square/`](./problems/22-maximal-square/)

```python
m = [["1","0","1","0","0"],["1","0","1","1","1"],["1","1","1","1","1"],["1","0","0","1","0"]]
assert maximal_square(m) == 4
```

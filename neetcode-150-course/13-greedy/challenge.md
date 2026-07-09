# Challenge 13 — Greedy

## Tasks

### 1. Jump Game II
[`problems/03-jump-game-ii/`](./problems/03-jump-game-ii/)

```python
assert jump([2, 3, 1, 1, 4]) == 2
assert jump([2, 3, 0, 1, 4]) == 2
```

### 2. Gas Station
[`problems/04-gas-station/`](./problems/04-gas-station/)

```python
assert can_complete_circuit([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]) == 3
assert can_complete_circuit([2, 3, 4], [3, 4, 3]) == -1
```

### 3. Valid Parenthesis String
[`problems/08-valid-parenthesis-string/`](./problems/08-valid-parenthesis-string/)

```python
assert check_valid_string("()") is True
assert check_valid_string("(*)") is True
assert check_valid_string("(*))") is True
assert check_valid_string("(((*)") is False
```

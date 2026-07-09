# Challenge 07 — Trees

Solutions live next to each problem in `solutions/`.

## Tasks

Three problems, both languages.

### 1. Validate Binary Search Tree
[`problems/07-validate-binary-search-tree/`](./problems/07-validate-binary-search-tree/)

```python
assert is_valid_bst(from_array([2, 1, 3])) is True
assert is_valid_bst(from_array([5, 1, 4, None, None, 3, 6])) is False
assert is_valid_bst(from_array([])) is True
```

### 2. Level Order Traversal
[`problems/10-binary-tree-level-order-traversal/`](./problems/10-binary-tree-level-order-traversal/)

```python
assert level_order(from_array([3, 9, 20, None, None, 15, 7])) == [[3], [9, 20], [15, 7]]
assert level_order(from_array([1])) == [[1]]
```

### 3. Maximum Path Sum (hard)
[`problems/15-binary-tree-maximum-path-sum/`](./problems/15-binary-tree-maximum-path-sum/)

```python
assert max_path_sum(from_array([1, 2, 3])) == 6
assert max_path_sum(from_array([-10, 9, 20, None, None, 15, 7])) == 42
assert max_path_sum(from_array([-3])) == -3
```

## Success criteria

- [ ] All three Python files pass.
- [ ] All three Java files compile and print the expected values.
- [ ] Validate BST is O(n); the others are O(n) too.

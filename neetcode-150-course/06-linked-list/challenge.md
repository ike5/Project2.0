# Challenge 06 — Linked List

Solutions live next to each problem in `solutions/`.

## Tasks

Three problems, both languages. Use the `build_list` and `to_array`
helpers from the lab.

### 1. Reorder List
[`problems/03-reorder-list/`](./problems/03-reorder-list/)

```python
assert to_array(reorder_list(build_list([1, 2, 3, 4]))) == [1, 4, 2, 3]
assert to_array(reorder_list(build_list([1, 2, 3, 4, 5]))) == [1, 5, 2, 4, 3]
```

### 2. Linked List Cycle
[`problems/07-linked-list-cycle/`](./problems/07-linked-list-cycle/)

```python
# head = [3,2,0,-4] with cycle back to index 1
n0 = ListNode(3); n1 = ListNode(2); n2 = ListNode(0); n3 = ListNode(-4)
n0.next = n1; n1.next = n2; n2.next = n3; n3.next = n1
assert has_cycle(n0) is True

# head = [1,2], no cycle
n0 = ListNode(1); n1 = ListNode(2); n0.next = n1
assert has_cycle(n0) is False
```

### 3. Reverse Nodes in k-Group (hard)
[`problems/11-reverse-nodes-in-k-group/`](./problems/11-reverse-nodes-in-k-group/)

```python
assert to_array(reverse_k_group(build_list([1, 2, 3, 4, 5]), 2)) == [2, 1, 4, 3, 5]
assert to_array(reverse_k_group(build_list([1, 2, 3, 4, 5]), 3)) == [3, 2, 1, 4, 5]
```

## Success criteria

- [ ] All three Python files pass.
- [ ] All three Java files compile and print the expected values.
- [ ] Each solution uses O(1) extra space (besides the new list / output).

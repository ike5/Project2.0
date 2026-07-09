# Challenge 04 — Stack

Solutions live next to each problem in `solutions/`.

## Tasks

Three problems, both languages.

### 1. Min Stack
[`problems/02-min-stack/`](./problems/02-min-stack/)

```python
s = MinStack()
s.push(-2); s.push(0); s.push(-3)
assert s.get_min() == -3
s.pop()
assert s.top() == 0
assert s.get_min() == -2
```

### 2. Evaluate Reverse Polish Notation
[`problems/03-evaluate-reverse-polish-notation/`](./problems/03-evaluate-reverse-polish-notation/)

```python
assert eval_rpn(["2", "1", "+", "3", "*"]) == 9
assert eval_rpn(["4", "13", "5", "/", "+"]) == 6
```

### 3. Largest Rectangle in Histogram (hard)
[`problems/07-largest-rectangle-in-histogram/`](./problems/07-largest-rectangle-in-histogram/)

```python
assert largest_rectangle_area([2, 1, 5, 6, 2, 3]) == 10
assert largest_rectangle_area([2, 4]) == 4
```

## Success criteria

- [ ] All three Python files pass.
- [ ] All three Java files compile and print the expected values.
- [ ] `MinStack` operations are all O(1).

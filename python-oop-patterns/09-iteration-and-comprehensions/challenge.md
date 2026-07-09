# Challenge 09 — Iteration & comprehensions

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Implement `group_anagrams`** in `09-iteration-and-comprehensions/code/group_anagrams_mine.py` from scratch. Submit to LeetCode 49. Bonus: use a `tuple(sorted(s))` as the key, or a `Counter` — both work.
2. **Build `top_k_frequent(nums, k)`** (LeetCode 347). Use `Counter` + `heapq.nlargest(k, counter.items(), key=lambda kv: kv[1])`. Or sort the counter's items by frequency descending.
3. **Build `longest_common_prefix(strs)`** (LeetCode 14). The proper version: compare characters position by position using `zip(*strs)`. Use a generator.
4. **Write `pytest` tests** for all three in `09-iteration-and-comprehensions/code/test_mine.py`.

## Success criteria

- [ ] LeetCode 49 accepts your `group_anagrams`.
- [ ] `top_k_frequent([1,1,1,2,2,3], 2) == [1, 2]`.
- [ ] `longest_common_prefix(["flower", "flow", "flight"]) == "fl"`.
- [ ] All tests pass.

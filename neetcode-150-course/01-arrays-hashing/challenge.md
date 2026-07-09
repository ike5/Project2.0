# Challenge 01 — Arrays & Hashing

Solutions in [`solutions/`](./solutions/) (per problem) and a worked example
for the first one in [`solutions/01-contains-duplicate/`](./solutions/01-contains-duplicate/).
Try the lab first; only peek if you're stuck.

## Tasks

You have three problems to do **without** looking at the solutions. Each one
has Python and Java versions.

### 1. Two Sum

See [`problems/03-two-sum/`](./problems/03-two-sum/).

Create `01-arrays-hashing/challenge_two_sum.py` and
`01-arrays-hashing/challenge_two_sum.java` (class `ChallengeTwoSum`).

✅ Both should pass:

```python
assert two_sum([2, 7, 11, 15], 9) == [0, 1]
assert two_sum([3, 2, 4], 6) == [1, 2]
assert two_sum([3, 3], 6) == [0, 1]
```

```java
// expected: [0, 1], [1, 2], [0, 1]
```

### 2. Group Anagrams

See [`problems/04-group-anagrams/`](./problems/04-group-anagrams/).

Create `01-arrays-hashing/challenge_group_anagrams.py` and
`01-arrays-hashing/challenge_group_anagrams.java` (class
`ChallengeGroupAnagrams`).

✅ The output for `["eat","tea","tan","ate","nat","bat"]` should group
`"bat"`, `["tan","nat"]`, and `["ate","eat","tea"]` (order may vary).

### 3. Longest Consecutive Sequence

See [`problems/09-longest-consecutive-sequence/`](./problems/09-longest-consecutive-sequence/).

Create `01-arrays-hashing/challenge_longest_consecutive.py` and
`01-arrays-hashing/challenge_longest_consecutive.java` (class
`ChallengeLongestConsecutive`).

✅ All must finish in O(n) time. Tests:

```python
assert longest_consecutive([100, 4, 200, 1, 3, 2]) == 4
assert longest_consecutive([0, 3, 7, 2, 5, 8, 4, 6, 0, 1]) == 9
assert longest_consecutive([]) == 0
```

## Success criteria

- [ ] All three Python files compile and pass their asserts.
- [ ] All three Java files compile and pass their asserts (`-ea`).
- [ ] Each solution runs in O(n) time (you can use `time.perf_counter` /
      `System.nanoTime` to spot-check).

# Module 01 — Arrays & Hashing 🗂️

**Goal:** master the most common interview pattern: scan an array and use a
**hash map** or **hash set** to remember what you've seen. ⏱️ ~6 h · 🎯
Prereq: 00.

```
arrays + hash maps = the workhorse of 30%+ of interview problems
```

---

## 1. Why this module first?

Arrays and hash maps are the *lingua franca* of coding interviews. Three out of
the first five problems on the NeetCode 150 use only these two structures, and
the patterns you learn here reappear inside everything else: graphs use hash
maps for adjacency lists, DP uses them for memoization, sliding windows use them
for frequency counts. If you only ever learn one module, learn this one.

## 2. The two structures

| Structure | Python | Java 21 | When |
|-----------|--------|---------|------|
| Hash set | `set` | `Set<T>`, `HashSet<T>` | "Have I seen this before?" |
| Hash map | `dict` | `Map<K,V>`, `HashMap<K,V>` | "How many times / where / what value?" |

Both are amortized **O(1)** per operation. Use them whenever a brute-force
O(n²) solution involves repeated *lookups* ("does this value exist?", "where
did I last see it?").

## 3. The 9 problems — easy → hard

| #  | Problem | Difficulty | What it teaches |
|----|---------|-----------|-----------------|
| 01 | [Contains Duplicate](./problems/01-contains-duplicate/) | Easy | Set membership |
| 02 | [Valid Anagram](./problems/02-valid-anagram/) | Easy | Frequency count via map |
| 03 | [Two Sum](./problems/03-two-sum/) | Easy | "Where did I last see complement?" |
| 04 | [Group Anagrams](./problems/04-group-anagrams/) | Medium | Map keyed on canonical form |
| 05 | [Top K Frequent Elements](./problems/05-top-k-frequent-elements/) | Medium | Bucket sort by frequency |
| 06 | [Product of Array Except Self](./problems/06-product-of-array-except-self/) | Medium | Prefix-suffix product trick |
| 07 | [Valid Sudoku](./problems/07-valid-sudoku/) | Medium | Per-row/col/box validation with sets |
| 08 | [Encode and Decode Strings](./problems/08-encode-and-decode-strings/) | Medium | Length-prefixed serialization |
| 09 | [Longest Consecutive Sequence](./problems/09-longest-consecutive-sequence/) | Medium | Set lookup turns O(n log n) into O(n) |

> The last three on this list are *medium* in the official NeetCode ranking,
> but they introduce techniques (per-box scanning, serialization, the
> "set + extend" trick) that you'll reuse for the rest of the course.

## 4. The five patterns this module drills

1. **Set membership** — `if x in seen` (Python), `seen.contains(x)` (Java).
   *Contains Duplicate* uses this on its own.
2. **Frequency count** — `Counter` / `Map.merge(k, 1, Integer::sum)`.
   *Valid Anagram* uses this.
3. **Index-of-last-occurrence** — `dict[value] -> index`. *Two Sum* uses this.
4. **Map keyed on a canonical form** — `dict[tuple(sorted_chars)] -> list[str]`.
   *Group Anagrams* uses this.
5. **Set + extension** — put everything in a set, then for each `x` count
   upward while `x+1, x+2, ...` are in the set. *Longest Consecutive Sequence*
   uses this.

## 5. The Python / Java differences to know

| Concept | Python | Java 21 |
|---------|--------|---------|
| Set literal | `{1, 2, 3}` | `Set.of(1, 2, 3)` |
| Map literal | `{"a": 1}` | `Map.of("a", 1)` |
| Map default | `d.get(k, 0)` | `m.getOrDefault(k, 0)` |
| Map increment | `d[k] = d.get(k, 0) + 1` | `m.merge(k, 1, Integer::sum)` |
| Counter | `collections.Counter` | none — use a `Map<K,Integer>` |
| Sorting chars | `sorted(s)` | `s.chars().sorted()...` (boxed) |
| Length of int | `len(str(n))` | `String.valueOf(n).length()` |
| Integer overflow | never | watch products/sums of `int` |

## 6. How the module is structured

Each problem lives under `problems/NN-name/` (the brief) and
`solutions/NN-name/` (Python + Java + walkthrough). The `lab.md` works through
the first two problems *together* (Duplicate → Anagram) and the `challenge.md`
asks you to solve a problem you haven't seen. The `code/` folder has
*reference* solutions for the first two problems in case you want to peek.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

Then start working through the [problems/](./problems/) in order, peeking at
the [solutions/](./solutions/) only after you've tried.

## Key terms

hash set · hash map · `O(1)` amortized · `Counter` / `Map.merge` ·
frequency count · canonical form · set + extend

**Next →** [Module 02: Two Pointers](../02-two-pointers/)

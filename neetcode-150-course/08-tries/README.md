# Module 08 — Tries 🔤

**Goal:** use prefix trees for efficient prefix lookups. ⏱️ ~2 h · 🎯
Prereq: 07.

```
trie: O(len) insert/search/prefix — the right tool for "all words with prefix P"
```

---

## 1. What is a trie?

A **trie** (or prefix tree) is a tree where:

- Each edge is labeled with a character.
- Each node represents a prefix.
- The root represents the empty string.
- A flag (or a stored value) marks the end of a word.

Operations are O(len(word)). The cost is **O(Σ chars across all words)**
memory.

## 2. The 3 problems — medium → hard

| #  | Problem | Difficulty | Technique |
|----|---------|-----------|-----------|
| 01 | [Implement Trie (Prefix Tree)](./problems/01-implement-trie/) | Medium | Build, search, prefix |
| 02 | [Design Add and Search Words Data Structure](./problems/02-design-add-and-search-words-data-structure/) | Medium | Trie + DFS on `.` |
| 03 | [Word Search II](./problems/03-word-search-ii/) | Hard | Trie of words + DFS on board |

## 3. The Python / Java differences

| Concept | Python | Java |
|---------|--------|------|
| Children | `dict[str, dict]` or `dict[str, Node]` | `Node[26]` array |
| End marker | `node['#'] = True` or `node.word` | `node.isEnd` or `node.word` |
| Dot/wildcard | DFS with `node.values()` | DFS over all 26 children |
| Sort result | `sorted(out)` | `Collections.sort(out)` |

## 4. Common pitfalls

- **De-duplication.** Word Search II can find the same word multiple times.
  Clear the `word` field after finding once.
- **Board mutation.** Mark cells visited with `'#'` and unmark on the way
  back; otherwise you can re-use a cell.
- **26 vs dict children.** `Node[26]` is faster for ASCII lowercase but
  wastes memory if the alphabet is sparse. Use a dict for general alphabets.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

trie · prefix tree · end-of-word flag · DFS with backtracking

**Next →** [Module 09: Heap / Priority Queue](../09-heap-priority-queue/)

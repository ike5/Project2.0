# Implement Trie (Prefix Tree) - walkthrough

**Difficulty:** Medium &middot; **Module:** 08 Tries

## Brief

A trie (pronounced as 'try') or prefix tree is a tree data structure used to efficiently store and retrieve keys in a dataset of strings. Implement the Trie class: `insert(word)`, `search(word)`, and `starts_with(prefix)`.

## Examples

- `Trie(); insert('apple'); search('apple') -> True; search('app') -> False; starts_with('app') -> True` &rarr; `True, False, True`

## Constraints

- 1 <= word.length, prefix.length <= 2000
- word and prefix consist only of lowercase English letters
- At most 3 * 10^4 calls in total to insert, search, and starts_with

## Intuition

A trie is a tree of nodes, one per character. We mark the end of a
word with a flag.

Two implementations:

- **Python dict-of-dicts** (compact, no fixed alphabet size).
- **Java Node[26]** (faster, but assumes lowercase a-z).

**Time per op:** O(len(word)). **Space:** O(total chars across all words).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

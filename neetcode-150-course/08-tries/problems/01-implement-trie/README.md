# Implement Trie (Prefix Tree)

**Difficulty:** Medium

## Problem

A trie (pronounced as 'try') or prefix tree is a tree data structure used to efficiently store and retrieve keys in a dataset of strings. Implement the Trie class: `insert(word)`, `search(word)`, and `starts_with(prefix)`.

## Examples

```
Input:  Trie(); insert('apple'); search('apple') -> True; search('app') -> False; starts_with('app') -> True
Output: True, False, True
```

## Constraints

- 1 <= word.length, prefix.length <= 2000
- word and prefix consist only of lowercase English letters
- At most 3 * 10^4 calls in total to insert, search, and starts_with

## Hints

1. Each node has 26 children (one per letter) and an `is_end` flag.
2. insert: walk character by character, creating missing nodes.
3. search / starts_with: walk; return False if a node is missing.

## Solution

See [`../../solutions/01-implement-trie/`](../../solutions/01-implement-trie/) for the Python and Java 21 solutions and a step-by-step walkthrough.

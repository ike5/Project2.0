# Design Add and Search Words Data Structure

**Difficulty:** Medium

## Problem

Design a data structure that supports adding new words and finding if a string matches any previously added string. Implement the `WordDictionary` class: `add_word(word)` and `search(word)`. The search string can contain dots `.` where a dot matches any single letter.

## Examples

```
Input:  WordDictionary(); add_word('bad'); add_word('dad'); add_word('mad'); search('pad') -> False; search('bad') -> True; search('.ad') -> True; search('b..') -> True
Output: False, True, True, True
```

## Constraints

- 1 <= word.length <= 25
- add_word: at most 10^4 calls
- search: at most 10^4 calls

## Hints

1. Same trie structure. On `.`, try all 26 children (DFS).

## Solution

See [`../../solutions/02-design-add-and-search-words-data-structure/`](../../solutions/02-design-add-and-search-words-data-structure/) for the Python and Java 21 solutions and a step-by-step walkthrough.

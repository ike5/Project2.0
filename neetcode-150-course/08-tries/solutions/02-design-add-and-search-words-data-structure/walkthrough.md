# Design Add and Search Words Data Structure - walkthrough

**Difficulty:** Medium &middot; **Module:** 08 Tries

## Brief

Design a data structure that supports adding new words and finding if a string matches any previously added string. Implement the `WordDictionary` class: `add_word(word)` and `search(word)`. The search string can contain dots `.` where a dot matches any single letter.

## Examples

- `WordDictionary(); add_word('bad'); add_word('dad'); add_word('mad'); search('pad') -> False; search('bad') -> True; search('.ad') -> True; search('b..') -> True` &rarr; `False, True, True, True`

## Constraints

- 1 <= word.length <= 25
- add_word: at most 10^4 calls
- search: at most 10^4 calls

## Intuition

Same trie as before, but `search` recurses: on a `.` it tries all
26 children. Worst case O(26^n) where n is the word length with all
dots; in practice much faster.

**Time:** add O(len), search O(26^dots · len). **Space:** O(total chars).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

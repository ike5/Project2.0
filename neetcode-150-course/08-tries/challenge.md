# Challenge 08 — Tries

## Tasks

Two problems.

### 1. Design Add and Search Words
[`problems/02-design-add-and-search-words-data-structure/`](./problems/02-design-add-and-search-words-data-structure/)

```python
wd = WordDictionary()
wd.add_word("bad"); wd.add_word("dad"); wd.add_word("mad")
assert wd.search("pad") is False
assert wd.search("bad") is True
assert wd.search(".ad") is True
assert wd.search("b..") is True
```

### 2. Word Search II (hard)
[`problems/03-word-search-ii/`](./problems/03-word-search-ii/)

```python
board = [["o","a","a","n"],
         ["e","t","a","e"],
         ["i","h","k","r"],
         ["i","f","l","v"]]
words = ["oath","pea","eat","rain"]
assert sorted(find_words(board, words)) == ["eat", "oath"]
```

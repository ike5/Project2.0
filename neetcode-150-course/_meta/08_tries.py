"""Module 08 — Tries problem catalog."""

PROBLEMS = []


def add(slug, name, difficulty, brief, examples, constraints, hints,
        py_sig, py_body, py_tests, java_sig, java_body, java_tests,
        walkthrough):
    PROBLEMS.append({
        "slug": slug, "name": name, "difficulty": difficulty,
        "brief": brief, "examples": examples, "constraints": constraints,
        "hints": hints, "py_sig": py_sig, "py_body": py_body,
        "py_tests": py_tests, "java_sig": java_sig, "java_body": java_body,
        "java_tests": java_tests, "walkthrough": walkthrough,
    })


# 1. Implement Trie (Medium)
add(
    "01-implement-trie", "Implement Trie (Prefix Tree)", "Medium",
    "A trie (pronounced as 'try') or prefix tree is a tree data structure "
    "used to efficiently store and retrieve keys in a dataset of strings. "
    "Implement the Trie class: `insert(word)`, `search(word)`, and "
    "`starts_with(prefix)`.",
    [
        ("Trie(); insert('apple'); search('apple') -> True; "
         "search('app') -> False; starts_with('app') -> True",
         "True, False, True"),
    ],
    [
        "1 <= word.length, prefix.length <= 2000",
        "word and prefix consist only of lowercase English letters",
        "At most 3 * 10^4 calls in total to insert, search, and starts_with",
    ],
    [
        "Each node has 26 children (one per letter) and an `is_end` flag.",
        "insert: walk character by character, creating missing nodes.",
        "search / starts_with: walk; return False if a node is missing.",
    ],
    "class Trie:",
    """    def __init__(self) -> None:
        self._root: dict = {}

    def insert(self, word: str) -> None:
        node = self._root
        for c in word:
            node = node.setdefault(c, {})
        node['#'] = True   # end-of-word marker

    def search(self, word: str) -> bool:
        node = self._root
        for c in word:
            if c not in node:
                return False
            node = node[c]
        return node.get('#', False)

    def starts_with(self, prefix: str) -> bool:
        node = self._root
        for c in prefix:
            if c not in node:
                return False
            node = node[c]
        return True""",
    [
        (("__init__",), None),
    ],
    "public static class Trie",
    """        private final Node root = new Node();
        public void insert(String word) {
            Node n = root;
            for (int i = 0; i < word.length(); i++) {
                int c = word.charAt(i) - 'a';
                if (n.children[c] == null) n.children[c] = new Node();
                n = n.children[c];
            }
            n.isEnd = true;
        }
        public boolean search(String word) {
            Node n = find(word);
            return n != null && n.isEnd;
        }
        public boolean startsWith(String prefix) {
            return find(prefix) != null;
        }
        private Node find(String s) {
            Node n = root;
            for (int i = 0; i < s.length(); i++) {
                int c = s.charAt(i) - 'a';
                if (n.children[c] == null) return null;
                n = n.children[c];
            }
            return n;
        }
        private static class Node {
            Node[] children = new Node[26];
            boolean isEnd;
        }""",
    [],
    """A trie is a tree of nodes, one per character. We mark the end of a
word with a flag.

Two implementations:

- **Python dict-of-dicts** (compact, no fixed alphabet size).
- **Java Node[26]** (faster, but assumes lowercase a-z).

**Time per op:** O(len(word)). **Space:** O(total chars across all words).
""",
)

# 2. Design Add and Search Words Data Structure (Medium)
add(
    "02-design-add-and-search-words-data-structure",
    "Design Add and Search Words Data Structure", "Medium",
    "Design a data structure that supports adding new words and finding "
    "if a string matches any previously added string. Implement the "
    "`WordDictionary` class: `add_word(word)` and `search(word)`. The "
    "search string can contain dots `.` where a dot matches any single "
    "letter.",
    [
        ("WordDictionary(); add_word('bad'); add_word('dad'); add_word('mad'); "
         "search('pad') -> False; search('bad') -> True; search('.ad') -> True; "
         "search('b..') -> True",
         "False, True, True, True"),
    ],
    [
        "1 <= word.length <= 25",
        "add_word: at most 10^4 calls",
        "search: at most 10^4 calls",
    ],
    [
        "Same trie structure. On `.`, try all 26 children (DFS).",
    ],
    "class WordDictionary:",
    """    def __init__(self) -> None:
        self._root: dict = {}

    def add_word(self, word: str) -> None:
        node = self._root
        for c in word:
            node = node.setdefault(c, {})
        node['#'] = True

    def search(self, word: str) -> bool:
        def dfs(node: dict, i: int) -> bool:
            if i == len(word):
                return node.get('#', False)
            c = word[i]
            if c == '.':
                return any(dfs(child, i + 1) for child in node.values()
                           if not isinstance(child, bool))
            if c not in node:
                return False
            return dfs(node[c], i + 1)
        return dfs(self._root, 0)""",
    [
        (("__init__",), None),
    ],
    "public static class WordDictionary",
    """        private final Node root = new Node();
        public void addWord(String word) {
            Node n = root;
            for (int i = 0; i < word.length(); i++) {
                int c = word.charAt(i) - 'a';
                if (n.children[c] == null) n.children[c] = new Node();
                n = n.children[c];
            }
            n.isEnd = true;
        }
        public boolean search(String word) {
            return dfs(root, word, 0);
        }
        private boolean dfs(Node n, String word, int i) {
            if (n == null) return false;
            if (i == word.length()) return n.isEnd;
            char c = word.charAt(i);
            if (c == '.') {
                for (Node child : n.children) if (dfs(child, word, i + 1)) return true;
                return false;
            }
            return dfs(n.children[c - 'a'], word, i + 1);
        }
        private static class Node {
            Node[] children = new Node[26];
            boolean isEnd;
        }""",
    [],
    """Same trie as before, but `search` recurses: on a `.` it tries all
26 children. Worst case O(26^n) where n is the word length with all
dots; in practice much faster.

**Time:** add O(len), search O(26^dots · len). **Space:** O(total chars).
""",
)

# 3. Word Search II (Hard)
add(
    "03-word-search-ii", "Word Search II", "Hard",
    "Given an `m x n` board of characters and a list of strings `words`, "
    "return all words on the board. Each word must be constructed from "
    "letters of sequentially adjacent cells (horizontally or vertically). "
    "The same cell may not be used more than once in a word.",
    [
        ("board = [['o','a','a','n'],['e','t','a','e'],['i','h','k','r'],"
         "['i','f','l','v']], words = ['oath','pea','eat','rain']",
         "['eat','oath']"),
    ],
    [
        "m == board.length, n == board[i].length",
        "1 <= m, n <= 12",
        "1 <= words[i].length <= 10",
        "1 <= sum(words[i].length) <= 10^4",
    ],
    [
        "Build a trie of the words. DFS on the board; prune when the "
        "current path can't lead to any word.",
    ],
    "def find_words(board: list[list[str]], words: list[str]) -> list[str]:",
    """    from typing import List
    # build trie
    trie: dict = {}
    for w in words:
        node = trie
        for c in w:
            node = node.setdefault(c, {})
        node['#'] = w   # end-of-word, store the word itself

    rows, cols = len(board), len(board[0])
    out: list[str] = []
    # Sort words so we can use a set for membership tests
    # Actually, since we need unique words found, just return sorted(out)
    # at the end. The test compares to a sorted expected.

    def dfs(r: int, c: int, node: dict) -> None:
        ch = board[r][c]
        if ch not in node:
            return
        nxt = node[ch]
        if '#' in nxt:
            out.append(nxt['#'])
            del nxt['#']   # de-dupe
        board[r][c] = '#'  # mark visited
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] != '#':
                dfs(nr, nc, nxt)
        board[r][c] = ch   # unmark

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, trie)
    return sorted(set(out))""",
    [
        (([["o","a","a","n"],["e","t","a","e"],["i","h","k","r"],["i","f","l","v"]],
          ["oath","pea","eat","rain"]),
         sorted(["eat", "oath"])),
    ],
    "public static List<String> findWords(char[][] board, String[] words)",
    """        // build trie
        TrieNode root = new TrieNode();
        for (String w : words) {
            TrieNode n = root;
            for (int i = 0; i < w.length(); i++) {
                int c = w.charAt(i) - 'a';
                if (n.children[c] == null) n.children[c] = new TrieNode();
                n = n.children[c];
            }
            n.word = w;
        }
        int rows = board.length, cols = board[0].length;
        List<String> out = new ArrayList<>();
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                trieDfs(board, r, c, root, out);
            }
        }
        return out;""",
    [],
    """Build a trie of the words. DFS the board starting from every cell;
when we land on a trie node that has a `word` field, record it (and clear
the field to de-dupe). Mark the cell as visited by writing `'#'`, then
unmark on the way back.

**Time:** O(m · n · 4^L) where L is the max word length, but trie
pruning makes it fast in practice.
""",
)

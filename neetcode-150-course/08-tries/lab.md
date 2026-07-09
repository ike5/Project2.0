# Lab 08 — Tries

**You'll:** implement *Implement Trie* in both languages, comparing
`dict[str, dict]` (Python) with `Node[26]` (Java). ⏱️ ~1 h.

---

## Part A — *Implement Trie* in Python

```python
class Trie:
    def __init__(self):
        # your code
        ...

    def insert(self, word):
        ...

    def search(self, word):
        ...

    def starts_with(self, prefix):
        ...


if __name__ == "__main__":
    t = Trie()
    t.insert("apple")
    assert t.search("apple") is True
    assert t.search("app") is False
    assert t.starts_with("app") is True
    t.insert("app")
    assert t.search("app") is True
    print("all tests passed")
```

**Walk-through:**

```python
class Trie:
    def __init__(self):
        self._root: dict = {}

    def insert(self, word: str) -> None:
        node = self._root
        for c in word:
            node = node.setdefault(c, {})
        node['#'] = True

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
        return True
```

Why `setdefault`? It returns the existing child or creates a new dict.
Why `'#'` as end-of-word marker? It's a key that can never be a normal
lowercase letter, so it doesn't clash.

## Part B — *Implement Trie* in Java 21

```java
public class LabTrie {
    public static class Trie {
        private final Node root = new Node();

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
            Node n = root;
            for (int i = 0; i < word.length(); i++) {
                int c = word.charAt(i) - 'a';
                if (n.children[c] == null) return false;
                n = n.children[c];
            }
            return n.isEnd;
        }

        public boolean startsWith(String prefix) {
            Node n = root;
            for (int i = 0; i < prefix.length(); i++) {
                int c = prefix.charAt(i) - 'a';
                if (n.children[c] == null) return false;
                n = n.children[c];
            }
            return true;
        }

        private static class Node {
            Node[] children = new Node[26];
            boolean isEnd;
        }
    }

    public static void main(String[] args) {
        Trie t = new Trie();
        t.insert("apple");
        assert t.search("apple");
        assert !t.search("app");
        assert t.startsWith("app");
        t.insert("app");
        assert t.search("app");
        System.out.println("all tests passed");
    }
}
```

## What you learned

- **Trie as nested dicts** (Python) vs. **array of 26 children** (Java).
- **End-of-word marker** as a special key.
- **All operations are O(len(word))**.

➡️ **[challenge.md](./challenge.md)**

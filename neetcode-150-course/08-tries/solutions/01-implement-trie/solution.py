"""Implement Trie (Prefix Tree).

NeetCode 150 — auto-generated solution.

Run:
    python solutions/01-implement-trie/solution.py
"""



class Trie:
    def __init__(self) -> None:
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
        return True


def _self_test() -> None:
    pass  # no tests
    print(f"all 0 tests passed for Trie")


if __name__ == "__main__":
    _self_test()

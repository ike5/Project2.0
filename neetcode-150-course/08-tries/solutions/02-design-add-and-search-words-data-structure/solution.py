"""Design Add and Search Words Data Structure.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/02-design-add-and-search-words-data-structure/solution.py
"""



class WordDictionary:
    def __init__(self) -> None:
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
        return dfs(self._root, 0)


def _self_test() -> None:
    pass  # no tests
    print(f"all 0 tests passed for WordDictionary")


if __name__ == "__main__":
    _self_test()

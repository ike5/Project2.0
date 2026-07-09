"""Word Search II.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/03-word-search-ii/solution.py
"""



def find_words(board: list[list[str]], words: list[str]) -> list[str]:
    from typing import List
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
    return sorted(set(out))


def _self_test() -> None:
    assert find_words([['o', 'a', 'a', 'n'], ['e', 't', 'a', 'e'], ['i', 'h', 'k', 'r'], ['i', 'f', 'l', 'v']], ['oath', 'pea', 'eat', 'rain']) == ['eat', 'oath'], f"test 1 failed: got { find_words([['o', 'a', 'a', 'n'], ['e', 't', 'a', 'e'], ['i', 'h', 'k', 'r'], ['i', 'f', 'l', 'v']], ['oath', 'pea', 'eat', 'rain'])!r } expected { ['eat', 'oath']!r }"
    print(f"all 1 tests passed for find_words")


if __name__ == "__main__":
    _self_test()

"""Palindrome Partitioning.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/07-palindrome-partitioning/solution.py
"""



def partition(s: str) -> list[list[str]]:
    n = len(s)
    # palindrome table
    is_pal = [[False] * n for _ in range(n)]
    for i in range(n - 1, -1, -1):
        for j in range(i, n):
            if s[i] == s[j] and (j - i < 2 or is_pal[i + 1][j - 1]):
                is_pal[i][j] = True
    out: list[list[str]] = []

    def backtrack(i: int, path: list[str]) -> None:
        if i == n:
            out.append(path.copy())
            return
        for j in range(i, n):
            if is_pal[i][j]:
                path.append(s[i:j + 1])
                backtrack(j + 1, path)
                path.pop()

    backtrack(0, [])
    return out


def _self_test() -> None:
    assert sorted([sorted(g) for g in partition('aab')]) == sorted([sorted(g) for g in [['a', 'a', 'b'], ['aa', 'b']]]), f"test 1 failed: got { sorted([sorted(g) for g in partition('aab')])!r } expected { sorted([sorted(g) for g in [['a', 'a', 'b'], ['aa', 'b']]])!r }"
    assert sorted([sorted(g) for g in partition('a')]) == sorted([sorted(g) for g in [['a']]]), f"test 2 failed: got { sorted([sorted(g) for g in partition('a')])!r } expected { sorted([sorted(g) for g in [['a']]])!r }"
    print(f"all 2 tests passed for partition")


if __name__ == "__main__":
    _self_test()

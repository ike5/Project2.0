"""Surrounded Regions.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/07-surrounded-regions/solution.py
"""



def solve(board: list[list[str]]) -> list[list[str]]:
    rows, cols = len(board), len(board[0])

    def dfs(r: int, c: int) -> None:
        if r < 0 or c < 0 or r >= rows or c >= cols or board[r][c] != 'O':
            return
        board[r][c] = '#'
        dfs(r + 1, c); dfs(r - 1, c); dfs(r, c + 1); dfs(r, c - 1)

    for r in range(rows):
        for c in (0, cols - 1):
            if board[r][c] == 'O':
                dfs(r, c)
    for c in range(cols):
        for r in (0, rows - 1):
            if board[r][c] == 'O':
                dfs(r, c)
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 'O':
                board[r][c] = 'X'
            elif board[r][c] == '#':
                board[r][c] = 'O'
    return board


def _self_test() -> None:
    assert sorted([sorted(g) for g in solve([['X', 'X', 'X', 'X'], ['X', 'O', 'O', 'X'], ['X', 'X', 'O', 'X'], ['X', 'O', 'X', 'X']])]) == sorted([sorted(g) for g in [['X', 'X', 'X', 'X'], ['X', 'X', 'X', 'X'], ['X', 'X', 'X', 'X'], ['X', 'O', 'X', 'X']]]), f"test 1 failed: got { sorted([sorted(g) for g in solve([['X', 'X', 'X', 'X'], ['X', 'O', 'O', 'X'], ['X', 'X', 'O', 'X'], ['X', 'O', 'X', 'X']])])!r } expected { sorted([sorted(g) for g in [['X', 'X', 'X', 'X'], ['X', 'X', 'X', 'X'], ['X', 'X', 'X', 'X'], ['X', 'O', 'X', 'X']]])!r }"
    print(f"all 1 tests passed for solve")


if __name__ == "__main__":
    _self_test()

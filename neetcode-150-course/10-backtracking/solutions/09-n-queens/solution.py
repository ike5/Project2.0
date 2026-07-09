"""N-Queens.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/09-n-queens/solution.py
"""



def solve_n_queens(n: int) -> list[list[str]]:
    cols: set[int] = set()
    diag1: set[int] = set()   # r - c
    diag2: set[int] = set()   # r + c
    out: list[list[str]] = []
    board: list[list[str]] = [['.'] * n for _ in range(n)]

    def backtrack(r: int) -> None:
        if r == n:
            out.append([''.join(row) for row in board])
            return
        for c in range(n):
            if c in cols or (r - c) in diag1 or (r + c) in diag2:
                continue
            board[r][c] = 'Q'
            cols.add(c); diag1.add(r - c); diag2.add(r + c)
            backtrack(r + 1)
            board[r][c] = '.'
            cols.remove(c); diag1.remove(r - c); diag2.remove(r + c)

    backtrack(0)
    return out


def _self_test() -> None:
    assert sorted([sorted(g) for g in solve_n_queens(4)]) == sorted([sorted(g) for g in [['.Q..', '...Q', 'Q...', '..Q.'], ['..Q.', 'Q...', '...Q', '.Q..']]]), f"test 1 failed: got { sorted([sorted(g) for g in solve_n_queens(4)])!r } expected { sorted([sorted(g) for g in [['.Q..', '...Q', 'Q...', '..Q.'], ['..Q.', 'Q...', '...Q', '.Q..']]])!r }"
    assert sorted([sorted(g) for g in solve_n_queens(1)]) == sorted([sorted(g) for g in [['Q']]]), f"test 2 failed: got { sorted([sorted(g) for g in solve_n_queens(1)])!r } expected { sorted([sorted(g) for g in [['Q']]])!r }"
    print(f"all 2 tests passed for solve_n_queens")


if __name__ == "__main__":
    _self_test()

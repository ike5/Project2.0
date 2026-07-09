"""Rotting Oranges.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/05-rotting-oranges/solution.py
"""



def oranges_rotting(grid: list[list[int]]) -> int:
    from collections import deque
    rows, cols = len(grid), len(grid[0])
    q: deque[tuple[int, int]] = deque()
    fresh = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2:
                q.append((r, c))
            elif grid[r][c] == 1:
                fresh += 1
    minutes = 0
    while q and fresh:
        for _ in range(len(q)):
            r, c = q.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                    grid[nr][nc] = 2
                    fresh -= 1
                    q.append((nr, nc))
        minutes += 1
    return minutes if fresh == 0 else -1


def _self_test() -> None:
    assert oranges_rotting([[2, 1, 1], [1, 1, 0], [0, 1, 1]]) == 4, f"test 1 failed: got { oranges_rotting([[2, 1, 1], [1, 1, 0], [0, 1, 1]])!r } expected { 4!r }"
    assert oranges_rotting([[2, 1, 1], [0, 1, 1], [1, 0, 1]]) == -1, f"test 2 failed: got { oranges_rotting([[2, 1, 1], [0, 1, 1], [1, 0, 1]])!r } expected { -1!r }"
    assert oranges_rotting([[0, 2]]) == 0, f"test 3 failed: got { oranges_rotting([[0, 2]])!r } expected { 0!r }"
    print(f"all 3 tests passed for oranges_rotting")


if __name__ == "__main__":
    _self_test()

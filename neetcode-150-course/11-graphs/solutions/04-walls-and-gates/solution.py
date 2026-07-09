"""Walls and Gates.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/04-walls-and-gates/solution.py
"""



def walls_and_gates(rooms: list[list[int]]) -> list[list[int]]:
    INF = 2 ** 31 - 1
    rows, cols = len(rooms), len(rooms[0])
    from collections import deque
    q: deque[tuple[int, int]] = deque()
    for r in range(rows):
        for c in range(cols):
            if rooms[r][c] == 0:
                q.append((r, c))
    while q:
        r, c = q.popleft()
        d = rooms[r][c]
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and rooms[nr][nc] == INF:
                rooms[nr][nc] = d + 1
                q.append((nr, nc))
    return rooms


def _self_test() -> None:
    assert sorted([sorted(g) for g in walls_and_gates([[2147483647, -1, 0, 2147483647], [2147483647, 2147483647, 2147483647, -1], [2147483647, -1, 2147483647, -1], [0, -1, 2147483647, 2147483647]])]) == sorted([sorted(g) for g in [[3, -1, 0, 1], [2, 2, 1, -1], [1, -1, 2, -1], [0, -1, 3, 4]]]), f"test 1 failed: got { sorted([sorted(g) for g in walls_and_gates([[2147483647, -1, 0, 2147483647], [2147483647, 2147483647, 2147483647, -1], [2147483647, -1, 2147483647, -1], [0, -1, 2147483647, 2147483647]])])!r } expected { sorted([sorted(g) for g in [[3, -1, 0, 1], [2, 2, 1, -1], [1, -1, 2, -1], [0, -1, 3, 4]]])!r }"
    print(f"all 1 tests passed for walls_and_gates")


if __name__ == "__main__":
    _self_test()

"""Pacific Atlantic Water Flow.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/06-pacific-atlantic-water-flow/solution.py
"""



def pacific_atlantic(heights: list[list[int]]) -> list[list[int]]:
    rows, cols = len(heights), len(heights[0])
    from collections import deque

    def bfs(starts: list[tuple[int, int]]) -> set[tuple[int, int]]:
        reachable: set[tuple[int, int]] = set(starts)
        q: deque[tuple[int, int]] = deque(starts)
        while q:
            r, c = q.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in reachable and heights[nr][nc] >= heights[r][c]:
                    reachable.add((nr, nc))
                    q.append((nr, nc))
        return reachable

    pacific = [(0, c) for c in range(cols)] + [(r, 0) for r in range(1, rows)]
    atlantic = [(rows - 1, c) for c in range(cols)] + [(r, cols - 1) for r in range(rows - 1)]
    pac = bfs(pacific)
    atl = bfs(atlantic)
    return [[r, c] for r, c in sorted(pac & atl)]


def _self_test() -> None:
    assert sorted([sorted(g) for g in pacific_atlantic([[1, 2, 2, 3, 5], [3, 2, 3, 4, 4], [2, 4, 5, 3, 1], [6, 7, 1, 4, 5], [5, 1, 1, 2, 4]])]) == sorted([sorted(g) for g in [[0, 4], [1, 3], [1, 4], [2, 2], [3, 0], [3, 1], [4, 0]]]), f"test 1 failed: got { sorted([sorted(g) for g in pacific_atlantic([[1, 2, 2, 3, 5], [3, 2, 3, 4, 4], [2, 4, 5, 3, 1], [6, 7, 1, 4, 5], [5, 1, 1, 2, 4]])])!r } expected { sorted([sorted(g) for g in [[0, 4], [1, 3], [1, 4], [2, 2], [3, 0], [3, 1], [4, 0]]])!r }"
    print(f"all 1 tests passed for pacific_atlantic")


if __name__ == "__main__":
    _self_test()

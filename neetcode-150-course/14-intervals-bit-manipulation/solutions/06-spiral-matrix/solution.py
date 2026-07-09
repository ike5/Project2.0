"""Spiral Matrix.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/06-spiral-matrix/solution.py
"""



def spiral_order(matrix: list[list[int]]) -> list[int]:
    out: list[int] = []
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        for j in range(left, right + 1):
            out.append(matrix[top][j])
        top += 1
        for i in range(top, bottom + 1):
            out.append(matrix[i][right])
        right -= 1
        if top <= bottom:
            for j in range(right, left - 1, -1):
                out.append(matrix[bottom][j])
            bottom -= 1
        if left <= right:
            for i in range(bottom, top - 1, -1):
                out.append(matrix[i][left])
            left += 1
    return out


def _self_test() -> None:
    assert spiral_order([[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == [1, 2, 3, 6, 9, 8, 7, 4, 5], f"test 1 failed: got { spiral_order([[1, 2, 3], [4, 5, 6], [7, 8, 9]])!r } expected { [1, 2, 3, 6, 9, 8, 7, 4, 5]!r }"
    assert spiral_order([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]]) == [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7], f"test 2 failed: got { spiral_order([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]])!r } expected { [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]!r }"
    print(f"all 2 tests passed for spiral_order")


if __name__ == "__main__":
    _self_test()

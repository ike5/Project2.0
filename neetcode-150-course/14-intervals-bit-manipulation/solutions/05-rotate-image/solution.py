"""Rotate Image.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/05-rotate-image/solution.py
"""



def rotate(matrix: list[list[int]]) -> list[list[int]]:
    n = len(matrix)
    # transpose
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    # reverse each row
    for row in matrix:
        row.reverse()
    return matrix


def _self_test() -> None:
    assert sorted([sorted(g) for g in rotate([[1, 2, 3], [4, 5, 6], [7, 8, 9]])]) == sorted([sorted(g) for g in [[7, 4, 1], [8, 5, 2], [9, 6, 3]]]), f"test 1 failed: got { sorted([sorted(g) for g in rotate([[1, 2, 3], [4, 5, 6], [7, 8, 9]])])!r } expected { sorted([sorted(g) for g in [[7, 4, 1], [8, 5, 2], [9, 6, 3]]])!r }"
    print(f"all 1 tests passed for rotate")


if __name__ == "__main__":
    _self_test()

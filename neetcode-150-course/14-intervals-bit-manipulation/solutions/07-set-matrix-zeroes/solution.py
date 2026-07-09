"""Set Matrix Zeroes.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/07-set-matrix-zeroes/solution.py
"""



def set_zeroes(matrix: list[list[int]]) -> list[list[int]]:
    m, n = len(matrix), len(matrix[0])
    first_row_zero = any(matrix[0][j] == 0 for j in range(n))
    first_col_zero = any(matrix[i][0] == 0 for i in range(m))
    # mark zeros in rest
    for i in range(1, m):
        for j in range(1, n):
            if matrix[i][j] == 0:
                matrix[i][0] = 0
                matrix[0][j] = 0
    # zero rows
    for i in range(1, m):
        if matrix[i][0] == 0:
            for j in range(n):
                matrix[i][j] = 0
    # zero cols
    for j in range(1, n):
        if matrix[0][j] == 0:
            for i in range(m):
                matrix[i][j] = 0
    # zero first row/col
    if first_row_zero:
        for j in range(n):
            matrix[0][j] = 0
    if first_col_zero:
        for i in range(m):
            matrix[i][0] = 0
    return matrix


def _self_test() -> None:
    assert sorted([sorted(g) for g in set_zeroes([[1, 1, 1], [1, 0, 1], [1, 1, 1]])]) == sorted([sorted(g) for g in [[1, 0, 1], [0, 0, 0], [1, 0, 1]]]), f"test 1 failed: got { sorted([sorted(g) for g in set_zeroes([[1, 1, 1], [1, 0, 1], [1, 1, 1]])])!r } expected { sorted([sorted(g) for g in [[1, 0, 1], [0, 0, 0], [1, 0, 1]]])!r }"
    print(f"all 1 tests passed for set_zeroes")


if __name__ == "__main__":
    _self_test()

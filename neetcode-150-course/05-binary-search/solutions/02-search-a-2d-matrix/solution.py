"""Search a 2D Matrix.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/02-search-a-2d-matrix/solution.py
"""



def search_matrix(matrix: list[list[int]], target: int) -> bool:
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    lo, hi = 0, m * n - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        v = matrix[mid // n][mid % n]
        if v == target:
            return True
        if v < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return False


def _self_test() -> None:
    assert search_matrix([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 3) == True, f"test 1 failed: got { search_matrix([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 3)!r } expected { True!r }"
    assert search_matrix([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 13) == False, f"test 2 failed: got { search_matrix([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 13)!r } expected { False!r }"
    print(f"all 2 tests passed for search_matrix")


if __name__ == "__main__":
    _self_test()

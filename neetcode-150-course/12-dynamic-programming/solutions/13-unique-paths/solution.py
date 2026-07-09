"""Unique Paths.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/13-unique-paths/solution.py
"""



def unique_paths(m: int, n: int) -> int:
    row = [1] * n
    for i in range(1, m):
        for j in range(1, n):
            row[j] += row[j - 1]
    return row[-1]


def _self_test() -> None:
    assert unique_paths(3, 7) == 28, f"test 1 failed: got { unique_paths(3, 7)!r } expected { 28!r }"
    assert unique_paths(3, 2) == 3, f"test 2 failed: got { unique_paths(3, 2)!r } expected { 3!r }"
    print(f"all 2 tests passed for unique_paths")


if __name__ == "__main__":
    _self_test()

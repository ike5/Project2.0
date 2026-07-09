"""Contains Duplicate.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/01-contains-duplicate/solution.py
"""



def contains_duplicate(nums: list[int]) -> bool:
    seen: set[int] = set()
    for x in nums:
        if x in seen:
            return True
        seen.add(x)
    return False


def _self_test() -> None:
    assert contains_duplicate([1, 2, 3, 1]) == True, f"test 1 failed: got { contains_duplicate([1, 2, 3, 1])!r } expected { True!r }"
    assert contains_duplicate([1, 2, 3, 4]) == False, f"test 2 failed: got { contains_duplicate([1, 2, 3, 4])!r } expected { False!r }"
    assert contains_duplicate([1, 1, 1, 3, 3, 4, 3, 2, 4, 2]) == True, f"test 3 failed: got { contains_duplicate([1, 1, 1, 3, 3, 4, 3, 2, 4, 2])!r } expected { True!r }"
    assert contains_duplicate([]) == False, f"test 4 failed: got { contains_duplicate([])!r } expected { False!r }"
    print(f"all 4 tests passed for contains_duplicate")


if __name__ == "__main__":
    _self_test()

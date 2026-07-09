"""Two Sum II — Input Array Is Sorted.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/02-two-sum-ii-input-array-is-sorted/solution.py
"""



def two_sum_sorted(numbers: list[int], target: int) -> list[int]:
    l, r = 0, len(numbers) - 1
    while l < r:
        s = numbers[l] + numbers[r]
        if s == target:
            return [l + 1, r + 1]   # 1-indexed
        if s < target:
            l += 1
        else:
            r -= 1
    return []


def _self_test() -> None:
    assert two_sum_sorted([2, 7, 11, 15], 9) == [1, 2], f"test 1 failed: got { two_sum_sorted([2, 7, 11, 15], 9)!r } expected { [1, 2]!r }"
    assert two_sum_sorted([2, 3, 4], 6) == [1, 3], f"test 2 failed: got { two_sum_sorted([2, 3, 4], 6)!r } expected { [1, 3]!r }"
    assert two_sum_sorted([-1, 0], -1) == [1, 2], f"test 3 failed: got { two_sum_sorted([-1, 0], -1)!r } expected { [1, 2]!r }"
    print(f"all 3 tests passed for two_sum_sorted")


if __name__ == "__main__":
    _self_test()

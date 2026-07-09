"""Two Sum.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/03-two-sum/solution.py
"""



def two_sum(nums: list[int], target: int) -> list[int]:
    seen: dict[int, int] = {}   # value -> index
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    return []


def _self_test() -> None:
    assert two_sum([2, 7, 11, 15], 9) == [0, 1], f"test 1 failed: got { two_sum([2, 7, 11, 15], 9)!r } expected { [0, 1]!r }"
    assert two_sum([3, 2, 4], 6) == [1, 2], f"test 2 failed: got { two_sum([3, 2, 4], 6)!r } expected { [1, 2]!r }"
    assert two_sum([3, 3], 6) == [0, 1], f"test 3 failed: got { two_sum([3, 3], 6)!r } expected { [0, 1]!r }"
    assert two_sum([-1, -2, -3, -4, -5], -8) == [2, 4], f"test 4 failed: got { two_sum([-1, -2, -3, -4, -5], -8)!r } expected { [2, 4]!r }"
    print(f"all 4 tests passed for two_sum")


if __name__ == "__main__":
    _self_test()

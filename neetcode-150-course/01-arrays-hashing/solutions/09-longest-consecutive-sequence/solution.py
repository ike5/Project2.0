"""Longest Consecutive Sequence.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/09-longest-consecutive-sequence/solution.py
"""



def longest_consecutive(nums: list[int]) -> int:
    s = set(nums)
    best = 0
    for x in s:
        if x - 1 in s:
            continue  # x is not the start of a run
        length = 1
        while x + length in s:
            length += 1
        best = max(best, length)
    return best


def _self_test() -> None:
    assert longest_consecutive([100, 4, 200, 1, 3, 2]) == 4, f"test 1 failed: got { longest_consecutive([100, 4, 200, 1, 3, 2])!r } expected { 4!r }"
    assert longest_consecutive([0, 3, 7, 2, 5, 8, 4, 6, 0, 1]) == 9, f"test 2 failed: got { longest_consecutive([0, 3, 7, 2, 5, 8, 4, 6, 0, 1])!r } expected { 9!r }"
    assert longest_consecutive([]) == 0, f"test 3 failed: got { longest_consecutive([])!r } expected { 0!r }"
    assert longest_consecutive([1, 2, 0, 1]) == 3, f"test 4 failed: got { longest_consecutive([1, 2, 0, 1])!r } expected { 3!r }"
    print(f"all 4 tests passed for longest_consecutive")


if __name__ == "__main__":
    _self_test()

"""Non-Overlapping Intervals.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/03-non-overlapping-intervals/solution.py
"""



def erase_overlap_intervals(intervals: list[list[int]]) -> int:
    intervals = sorted(intervals, key=lambda x: x[1])
    kept = 0
    end = float('-inf')
    for a, b in intervals:
        if a >= end:
            kept += 1
            end = b
    return len(intervals) - kept


def _self_test() -> None:
    assert erase_overlap_intervals([[1, 2], [2, 3], [3, 4], [1, 3]]) == 1, f"test 1 failed: got { erase_overlap_intervals([[1, 2], [2, 3], [3, 4], [1, 3]])!r } expected { 1!r }"
    assert erase_overlap_intervals([[1, 2], [1, 2], [1, 2]]) == 2, f"test 2 failed: got { erase_overlap_intervals([[1, 2], [1, 2], [1, 2]])!r } expected { 2!r }"
    assert erase_overlap_intervals([[1, 2], [2, 3]]) == 0, f"test 3 failed: got { erase_overlap_intervals([[1, 2], [2, 3]])!r } expected { 0!r }"
    print(f"all 3 tests passed for erase_overlap_intervals")


if __name__ == "__main__":
    _self_test()

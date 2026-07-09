"""Merge Intervals.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/02-merge-intervals/solution.py
"""



def merge(intervals: list[list[int]]) -> list[list[int]]:
    intervals = sorted(intervals)
    out: list[list[int]] = []
    for a, b in intervals:
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def _self_test() -> None:
    assert sorted([sorted(g) for g in merge([[1, 3], [2, 6], [8, 10], [15, 18]])]) == sorted([sorted(g) for g in [[1, 6], [8, 10], [15, 18]]]), f"test 1 failed: got { sorted([sorted(g) for g in merge([[1, 3], [2, 6], [8, 10], [15, 18]])])!r } expected { sorted([sorted(g) for g in [[1, 6], [8, 10], [15, 18]]])!r }"
    assert sorted([sorted(g) for g in merge([[1, 4], [4, 5]])]) == sorted([sorted(g) for g in [[1, 5]]]), f"test 2 failed: got { sorted([sorted(g) for g in merge([[1, 4], [4, 5]])])!r } expected { sorted([sorted(g) for g in [[1, 5]]])!r }"
    assert merge([]) == [], f"test 3 failed: got { merge([])!r } expected { []!r }"
    print(f"all 3 tests passed for merge")


if __name__ == "__main__":
    _self_test()

"""Insert Interval.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/01-insert-interval/solution.py
"""



def insert(intervals: list[list[int]], new_interval: list[int]) -> list[list[int]]:
    out: list[list[int]] = []
    for i, (a, b) in enumerate(intervals):
        if b < new_interval[0]:
            out.append([a, b])
        elif a > new_interval[1]:
            out.append(new_interval)
            out.extend(intervals[i:])
            return out
        else:
            new_interval = [min(a, new_interval[0]), max(b, new_interval[1])]
    out.append(new_interval)
    return out


def _self_test() -> None:
    assert sorted([sorted(g) for g in insert([[1, 3], [6, 9]], [2, 5])]) == sorted([sorted(g) for g in [[1, 5], [6, 9]]]), f"test 1 failed: got { sorted([sorted(g) for g in insert([[1, 3], [6, 9]], [2, 5])])!r } expected { sorted([sorted(g) for g in [[1, 5], [6, 9]]])!r }"
    assert sorted([sorted(g) for g in insert([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8])]) == sorted([sorted(g) for g in [[1, 2], [3, 10], [12, 16]]]), f"test 2 failed: got { sorted([sorted(g) for g in insert([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8])])!r } expected { sorted([sorted(g) for g in [[1, 2], [3, 10], [12, 16]]])!r }"
    print(f"all 2 tests passed for insert")


if __name__ == "__main__":
    _self_test()

"""Task Scheduler.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/05-task-scheduler/solution.py
"""



def least_interval(tasks: list[str], n: int) -> int:
    from collections import Counter
    counts = Counter(tasks)
    max_freq = max(counts.values())
    n_max = sum(1 for c in counts.values() if c == max_freq)
    return max(len(tasks), (max_freq - 1) * (n + 1) + n_max)


def _self_test() -> None:
    assert least_interval(['A', 'A', 'A', 'B', 'B', 'B'], 2) == 8, f"test 1 failed: got { least_interval(['A', 'A', 'A', 'B', 'B', 'B'], 2)!r } expected { 8!r }"
    assert least_interval(['A', 'A', 'A', 'B', 'B', 'B'], 0) == 6, f"test 2 failed: got { least_interval(['A', 'A', 'A', 'B', 'B', 'B'], 0)!r } expected { 6!r }"
    assert least_interval(['A', 'A', 'A', 'A', 'A', 'A', 'B', 'C', 'D', 'E', 'F', 'G'], 2) == 16, f"test 3 failed: got { least_interval(['A', 'A', 'A', 'A', 'A', 'A', 'B', 'C', 'D', 'E', 'F', 'G'], 2)!r } expected { 16!r }"
    print(f"all 3 tests passed for least_interval")


if __name__ == "__main__":
    _self_test()

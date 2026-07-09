"""Course Schedule.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/08-course-schedule/solution.py
"""



def can_finish(num_courses: int, prerequisites: list[list[int]]) -> bool:
    from collections import defaultdict, deque
    g: dict[int, list[int]] = defaultdict(list)
    indeg = [0] * num_courses
    for a, b in prerequisites:
        g[b].append(a)
        indeg[a] += 1
    q: deque[int] = deque(i for i in range(num_courses) if indeg[i] == 0)
    taken = 0
    while q:
        c = q.popleft()
        taken += 1
        for nb in g[c]:
            indeg[nb] -= 1
            if indeg[nb] == 0:
                q.append(nb)
    return taken == num_courses


def _self_test() -> None:
    assert can_finish(2, [[1, 0]]) == True, f"test 1 failed: got { can_finish(2, [[1, 0]])!r } expected { True!r }"
    assert can_finish(2, [[1, 0], [0, 1]]) == False, f"test 2 failed: got { can_finish(2, [[1, 0], [0, 1]])!r } expected { False!r }"
    assert can_finish(3, [[1, 0], [2, 1]]) == True, f"test 3 failed: got { can_finish(3, [[1, 0], [2, 1]])!r } expected { True!r }"
    print(f"all 3 tests passed for can_finish")


if __name__ == "__main__":
    _self_test()

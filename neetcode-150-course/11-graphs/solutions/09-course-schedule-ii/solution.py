"""Course Schedule II.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/09-course-schedule-ii/solution.py
"""



def find_order(num_courses: int, prerequisites: list[list[int]]) -> list[int]:
    from collections import defaultdict, deque
    g: dict[int, list[int]] = defaultdict(list)
    indeg = [0] * num_courses
    for a, b in prerequisites:
        g[b].append(a)
        indeg[a] += 1
    q: deque[int] = deque(i for i in range(num_courses) if indeg[i] == 0)
    order: list[int] = []
    while q:
        c = q.popleft()
        order.append(c)
        for nb in g[c]:
            indeg[nb] -= 1
            if indeg[nb] == 0:
                q.append(nb)
    return order if len(order) == num_courses else []


def _self_test() -> None:
    assert find_order(2, [[1, 0]]) == [0, 1], f"test 1 failed: got { find_order(2, [[1, 0]])!r } expected { [0, 1]!r }"
    assert find_order(4, [[1, 0], [2, 0], [3, 1], [3, 2]]) == [0, 1, 2, 3], f"test 2 failed: got { find_order(4, [[1, 0], [2, 0], [3, 1], [3, 2]])!r } expected { [0, 1, 2, 3]!r }"
    print(f"all 2 tests passed for find_order")


if __name__ == "__main__":
    _self_test()

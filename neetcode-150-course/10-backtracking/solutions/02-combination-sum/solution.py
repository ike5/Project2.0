"""Combination Sum.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/02-combination-sum/solution.py
"""



def combination_sum(candidates: list[int], target: int) -> list[list[int]]:
    out: list[list[int]] = []

    def backtrack(i: int, path: list[int], total: int) -> None:
        if total == target:
            out.append(path.copy())
            return
        if total > target or i == len(candidates):
            return
        # skip candidates[i]
        backtrack(i + 1, path, total)
        # include candidates[i] (re-use allowed, so we stay at i)
        path.append(candidates[i])
        backtrack(i, path, total + candidates[i])
        path.pop()

    backtrack(0, [], 0)
    return out


def _self_test() -> None:
    assert sorted([sorted(g) for g in combination_sum([2, 3, 6, 7], 7)]) == sorted([sorted(g) for g in [[2, 2, 3], [7]]]), f"test 1 failed: got { sorted([sorted(g) for g in combination_sum([2, 3, 6, 7], 7)])!r } expected { sorted([sorted(g) for g in [[2, 2, 3], [7]]])!r }"
    assert sorted([sorted(g) for g in combination_sum([2, 3, 5], 8)]) == sorted([sorted(g) for g in [[2, 2, 2, 2], [2, 3, 3], [3, 5]]]), f"test 2 failed: got { sorted([sorted(g) for g in combination_sum([2, 3, 5], 8)])!r } expected { sorted([sorted(g) for g in [[2, 2, 2, 2], [2, 3, 3], [3, 5]]])!r }"
    print(f"all 2 tests passed for combination_sum")


if __name__ == "__main__":
    _self_test()

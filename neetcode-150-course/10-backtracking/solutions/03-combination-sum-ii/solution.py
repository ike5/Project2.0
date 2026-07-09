"""Combination Sum II.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/03-combination-sum-ii/solution.py
"""



def combination_sum2(candidates: list[int], target: int) -> list[list[int]]:
    candidates = sorted(candidates)
    out: list[list[int]] = []

    def backtrack(i: int, path: list[int], total: int) -> None:
        if total == target:
            out.append(path.copy())
            return
        if total > target or i == len(candidates):
            return
        prev = -1
        for j in range(i, len(candidates)):
            if candidates[j] == prev:
                continue
            if total + candidates[j] > target:
                break
            path.append(candidates[j])
            backtrack(j + 1, path, total + candidates[j])
            path.pop()
            prev = candidates[j]

    backtrack(0, [], 0)
    return out


def _self_test() -> None:
    assert sorted([sorted(g) for g in combination_sum2([10, 1, 2, 7, 6, 1, 5], 8)]) == sorted([sorted(g) for g in [[1, 1, 6], [1, 2, 5], [1, 7], [2, 6]]]), f"test 1 failed: got { sorted([sorted(g) for g in combination_sum2([10, 1, 2, 7, 6, 1, 5], 8)])!r } expected { sorted([sorted(g) for g in [[1, 1, 6], [1, 2, 5], [1, 7], [2, 6]]])!r }"
    assert sorted([sorted(g) for g in combination_sum2([2, 5, 2, 1, 2], 5)]) == sorted([sorted(g) for g in [[1, 2, 2], [5]]]), f"test 2 failed: got { sorted([sorted(g) for g in combination_sum2([2, 5, 2, 1, 2], 5)])!r } expected { sorted([sorted(g) for g in [[1, 2, 2], [5]]])!r }"
    print(f"all 2 tests passed for combination_sum2")


if __name__ == "__main__":
    _self_test()

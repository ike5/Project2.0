"""Merge Triplets to Form Target Triplet.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/06-merge-triplets-to-form-target/solution.py
"""



def merge_triplets(triplets: list[list[int]], target: list[int]) -> bool:
    cur = [0, 0, 0]
    for t in triplets:
        if t[0] <= target[0] and t[1] <= target[1] and t[2] <= target[2]:
            cur = [max(cur[0], t[0]), max(cur[1], t[1]), max(cur[2], t[2])]
    return cur == target


def _self_test() -> None:
    assert merge_triplets([[2, 5, 3], [1, 8, 4], [1, 7, 5]], [2, 7, 5]) == True, f"test 1 failed: got { merge_triplets([[2, 5, 3], [1, 8, 4], [1, 7, 5]], [2, 7, 5])!r } expected { True!r }"
    assert merge_triplets([[3, 4, 5], [4, 5, 6]], [3, 2, 5]) == False, f"test 2 failed: got { merge_triplets([[3, 4, 5], [4, 5, 6]], [3, 2, 5])!r } expected { False!r }"
    print(f"all 2 tests passed for merge_triplets")


if __name__ == "__main__":
    _self_test()

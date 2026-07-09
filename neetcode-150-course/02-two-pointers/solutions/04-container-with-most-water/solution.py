"""Container With Most Water.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/04-container-with-most-water/solution.py
"""



def max_area(height: list[int]) -> int:
    l, r = 0, len(height) - 1
    best = 0
    while l < r:
        area = (r - l) * min(height[l], height[r])
        best = max(best, area)
        if height[l] < height[r]:
            l += 1
        else:
            r -= 1
    return best


def _self_test() -> None:
    assert max_area([1, 8, 6, 2, 5, 4, 8, 3, 7]) == 49, f"test 1 failed: got { max_area([1, 8, 6, 2, 5, 4, 8, 3, 7])!r } expected { 49!r }"
    assert max_area([1, 1]) == 1, f"test 2 failed: got { max_area([1, 1])!r } expected { 1!r }"
    assert max_area([4, 3, 2, 1, 4]) == 16, f"test 3 failed: got { max_area([4, 3, 2, 1, 4])!r } expected { 16!r }"
    print(f"all 3 tests passed for max_area")


if __name__ == "__main__":
    _self_test()

"""Trapping Rain Water.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/05-trapping-rain-water/solution.py
"""



def trap(height: list[int]) -> int:
    l, r = 0, len(height) - 1
    l_max = r_max = 0
    water = 0
    while l < r:
        if height[l] < height[r]:
            if height[l] >= l_max:
                l_max = height[l]
            else:
                water += l_max - height[l]
            l += 1
        else:
            if height[r] >= r_max:
                r_max = height[r]
            else:
                water += r_max - height[r]
            r -= 1
    return water


def _self_test() -> None:
    assert trap([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]) == 6, f"test 1 failed: got { trap([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1])!r } expected { 6!r }"
    assert trap([4, 2, 0, 3, 2, 5]) == 9, f"test 2 failed: got { trap([4, 2, 0, 3, 2, 5])!r } expected { 9!r }"
    assert trap([1, 0, 1]) == 1, f"test 3 failed: got { trap([1, 0, 1])!r } expected { 1!r }"
    print(f"all 3 tests passed for trap")


if __name__ == "__main__":
    _self_test()

"""Largest Rectangle in Histogram.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/07-largest-rectangle-in-histogram/solution.py
"""



def largest_rectangle_area(heights: list[int]) -> int:
    stack: list[int] = []   # indices, increasing heights
    best = 0
    for i, h in enumerate(heights + [0]):
        while stack and heights[stack[-1]] >= h:
            height = heights[stack.pop()]
            left = stack[-1] if stack else -1
            width = i - left - 1
            best = max(best, height * width)
        stack.append(i)
    return best


def _self_test() -> None:
    assert largest_rectangle_area([2, 1, 5, 6, 2, 3]) == 10, f"test 1 failed: got { largest_rectangle_area([2, 1, 5, 6, 2, 3])!r } expected { 10!r }"
    assert largest_rectangle_area([2, 4]) == 4, f"test 2 failed: got { largest_rectangle_area([2, 4])!r } expected { 4!r }"
    assert largest_rectangle_area([0]) == 0, f"test 3 failed: got { largest_rectangle_area([0])!r } expected { 0!r }"
    assert largest_rectangle_area([1, 1, 1, 1]) == 4, f"test 4 failed: got { largest_rectangle_area([1, 1, 1, 1])!r } expected { 4!r }"
    print(f"all 4 tests passed for largest_rectangle_area")


if __name__ == "__main__":
    _self_test()

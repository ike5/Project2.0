"""Sliding Window Maximum.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/06-sliding-window-maximum/solution.py
"""



def max_sliding_window(nums: list[int], k: int) -> list[int]:
    from collections import deque
    q: deque[int] = deque()   # indices, values decreasing
    out: list[int] = []
    for i, x in enumerate(nums):
        # drop indices whose value <= x (they can never be the max)
        while q and nums[q[-1]] <= x:
            q.pop()
        q.append(i)
        # drop indices that fell out of the window
        if q[0] <= i - k:
            q.popleft()
        # record max once the first full window is in
        if i >= k - 1:
            out.append(nums[q[0]])
    return out


def _self_test() -> None:
    assert max_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7], f"test 1 failed: got { max_sliding_window([1, 3, -1, -3, 5, 3, 6, 7], 3)!r } expected { [3, 3, 5, 5, 6, 7]!r }"
    assert max_sliding_window([1], 1) == [1], f"test 2 failed: got { max_sliding_window([1], 1)!r } expected { [1]!r }"
    assert max_sliding_window([9, 11], 2) == [11], f"test 3 failed: got { max_sliding_window([9, 11], 2)!r } expected { [11]!r }"
    print(f"all 3 tests passed for max_sliding_window")


if __name__ == "__main__":
    _self_test()

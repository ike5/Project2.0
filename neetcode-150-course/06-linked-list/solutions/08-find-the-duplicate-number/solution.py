"""Find the Duplicate Number.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/08-find-the-duplicate-number/solution.py
"""



def find_duplicate(nums: list[int]) -> int:
    # Floyd's on the implicit linked list
    slow = nums[0]
    fast = nums[0]
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    # find entry
    finder = nums[0]
    while finder != slow:
        finder = nums[finder]
        slow = nums[slow]
    return finder


def _self_test() -> None:
    assert find_duplicate([1, 3, 4, 2, 2]) == 2, f"test 1 failed: got { find_duplicate([1, 3, 4, 2, 2])!r } expected { 2!r }"
    assert find_duplicate([3, 1, 3, 4, 2]) == 3, f"test 2 failed: got { find_duplicate([3, 1, 3, 4, 2])!r } expected { 3!r }"
    assert find_duplicate([2, 2, 2, 2, 2]) == 2, f"test 3 failed: got { find_duplicate([2, 2, 2, 2, 2])!r } expected { 2!r }"
    print(f"all 3 tests passed for find_duplicate")


if __name__ == "__main__":
    _self_test()

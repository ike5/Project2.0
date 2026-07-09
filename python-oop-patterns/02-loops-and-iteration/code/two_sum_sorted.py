"""Two-pointer and hash-map versions of two-sum on a sorted list.

Run me: python 02-loops-and-iteration/code/two_sum_sorted.py
"""


def two_sum_sorted_two_pointer(nums: list[int], target: int) -> tuple[int, int] | None:
    left, right = 0, len(nums) - 1
    while left < right:
        s = nums[left] + nums[right]
        if s == target:
            return (left, right)
        if s < target:
            left += 1
        else:
            right -= 1
    return None


def two_sum_sorted_hashmap(nums: list[int], target: int) -> tuple[int, int] | None:
    seen: dict[int, int] = {}
    for i, x in enumerate(nums):
        if (need := target - x) in seen:
            return (seen[need], i)
        seen[x] = i
    return None


def main() -> None:
    nums = [-3, -1, 0, 1, 2, 4, 7]
    target = 5

    print("nums =", nums, "target =", target)
    print("two-pointer :", two_sum_sorted_two_pointer(nums, target))
    print("hash map    :", two_sum_sorted_hashmap(nums, target))

    assert two_sum_sorted_two_pointer(nums, target) == two_sum_sorted_hashmap(nums, target)


if __name__ == "__main__":
    main()

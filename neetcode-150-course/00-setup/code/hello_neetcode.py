"""Hello, NeetCode.

The simplest possible "Two Sum" to confirm the Python toolchain works.
Two Sum: given an array `nums` and a `target`, return the indices of the
two numbers that add up to target. We assume exactly one solution exists.

Run:
    python 00-setup/code/hello_neetcode.py
"""


def two_sum(nums: list[int], target: int) -> list[int]:
    seen: dict[int, int] = {}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    return []


def main() -> None:
    print("hello, neetcode")
    print(f"two_sum([2, 7, 11, 15], 9) -> {two_sum([2, 7, 11, 15], 9)}")
    print(f"two_sum([3, 2, 4], 6)        -> {two_sum([3, 2, 4], 6)}")
    print(f"two_sum([3, 3], 6)          -> {two_sum([3, 3], 6)}")


if __name__ == "__main__":
    main()

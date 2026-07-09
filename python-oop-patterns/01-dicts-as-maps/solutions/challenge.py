"""Reference solutions for challenge 01."""

from collections import Counter, defaultdict


def two_sum(nums: list[int], target: int) -> tuple[int, int] | None:
    seen: dict[int, int] = {}
    for i, x in enumerate(nums):
        if (need := target - x) in seen:
            return (seen[need], i)
        seen[x] = i
    return None


def first_unique_char(s: str) -> int:
    counts = Counter(s)
    for i, ch in enumerate(s):
        if counts[ch] == 1:
            return i
    return -1


def group_by_parity(nums: list[int]) -> dict[str, list[int]]:
    groups: defaultdict[str, list[int]] = defaultdict(list)
    for x in nums:
        groups["even" if x % 2 == 0 else "odd"].append(x)
    return dict(groups)

"""Reference solutions for challenge 02."""


def max_profit(prices: list[int]) -> int:
    min_sofar = prices[0]
    best = 0
    for price in prices[1:]:
        if price < min_sofar:
            min_sofar = price
        elif price - min_sofar > best:
            best = price - min_sofar
    return best


def two_sum_ii(nums: list[int], target: int) -> list[int]:
    """LeetCode 167 — 1-indexed, sorted input, two-pointer."""
    left, right = 0, len(nums) - 1
    while left < right:
        s = nums[left] + nums[right]
        if s == target:
            return [left + 1, right + 1]
        if s < target:
            left += 1
        else:
            right -= 1
    return []


def length_of_longest_substring(s: str) -> int:
    last: dict[str, int] = {}
    left = 0
    best = 0
    for right, ch in enumerate(s):
        if ch in last and last[ch] >= left:
            left = last[ch] + 1
        last[ch] = right
        if right - left + 1 > best:
            best = right - left + 1
    return best

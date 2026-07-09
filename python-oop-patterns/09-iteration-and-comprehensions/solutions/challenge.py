"""Reference solutions for challenge 09."""

from collections import Counter, defaultdict
import heapq


def group_anagrams(strs: list[str]) -> list[list[str]]:
    groups: defaultdict[str, list[str]] = defaultdict(list)
    for s in strs:
        groups["".join(sorted(s))].append(s)
    return list(groups.values())


def group_anagrams_counter(strs: list[str]) -> list[list[str]]:
    groups: defaultdict[tuple, list[str]] = defaultdict(list)
    for s in strs:
        groups[tuple(sorted(Counter(s).items()))].append(s)
    return list(groups.values())


def top_k_frequent(nums: list[int], k: int) -> list[int]:
    counts = Counter(nums)
    return [x for x, _ in heapq.nlargest(k, counts.items(), key=lambda kv: kv[1])]


def longest_common_prefix(strs: list[str]) -> str:
    if not strs:
        return ""
    for i, chars in enumerate(zip(*strs)):
        if len(set(chars)) > 1:
            return strs[0][:i]
    return min(strs, key=len)

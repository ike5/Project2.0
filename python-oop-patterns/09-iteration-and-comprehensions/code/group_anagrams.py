"""LeetCode 49 — Group Anagrams.

Run me: python 09-iteration-and-comprehensions/code/group_anagrams.py
"""

from collections import defaultdict


def group_anagrams(strs: list[str]) -> list[list[str]]:
    groups: defaultdict[str, list[str]] = defaultdict(list)
    for s in strs:
        key = "".join(sorted(s))
        groups[key].append(s)
    return list(groups.values())


def main() -> None:
    strs = ["eat", "tea", "tan", "ate", "nat", "bat"]
    result = group_anagrams(strs)
    for group in result:
        print(sorted(group))


if __name__ == "__main__":
    main()

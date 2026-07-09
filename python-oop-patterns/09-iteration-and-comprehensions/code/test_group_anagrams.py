"""pytest tests for group_anagrams."""

from group_anagrams import group_anagrams


def _normalize(groups: list[list[str]]) -> list[tuple[str, ...]]:
    return sorted(tuple(sorted(g)) for g in groups)


def test_basic():
    strs = ["eat", "tea", "tan", "ate", "nat", "bat"]
    expected = [("ate", "eat", "tea"), ("bat",), ("nat", "tan")]
    assert _normalize(group_anagrams(strs)) == expected


def test_empty():
    assert group_anagrams([]) == []


def test_single():
    assert _normalize(group_anagrams(["abc"])) == [("abc",)]


def test_all_anagrams():
    strs = ["abc", "bca", "cab"]
    assert _normalize(group_anagrams(strs)) == [("abc", "bca", "cab")]

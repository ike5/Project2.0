"""Lab 01D — Valid Anagram (reference solution)."""


def is_anagram(s: str, t: str) -> bool:
    from collections import Counter
    return Counter(s) == Counter(t)


if __name__ == "__main__":
    assert is_anagram("anagram", "nagaram") is True
    assert is_anagram("rat", "car") is False
    assert is_anagram("a", "a") is True
    assert is_anagram("ab", "a") is False
    assert is_anagram("", "") is True
    print("all tests passed")

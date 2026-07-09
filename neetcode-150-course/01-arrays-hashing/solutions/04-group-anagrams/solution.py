"""Group Anagrams.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/04-group-anagrams/solution.py
"""



def group_anagrams(strs: list[str]) -> list[list[str]]:
    from collections import defaultdict
    groups: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for s in strs:
        key = tuple(sorted(s))
        groups[key].append(s)
    return list(groups.values())


def _self_test() -> None:
    assert sorted([sorted(g) for g in group_anagrams(['eat', 'tea', 'tan', 'ate', 'nat', 'bat'])]) == sorted([sorted(g) for g in [['bat'], ['nat', 'tan'], ['ate', 'eat', 'tea']]]), f"test 1 failed: got { sorted([sorted(g) for g in group_anagrams(['eat', 'tea', 'tan', 'ate', 'nat', 'bat'])])!r } expected { sorted([sorted(g) for g in [['bat'], ['nat', 'tan'], ['ate', 'eat', 'tea']]])!r }"
    assert sorted([sorted(g) for g in group_anagrams([''])]) == sorted([sorted(g) for g in [['']]]), f"test 2 failed: got { sorted([sorted(g) for g in group_anagrams([''])])!r } expected { sorted([sorted(g) for g in [['']]])!r }"
    assert sorted([sorted(g) for g in group_anagrams(['a'])]) == sorted([sorted(g) for g in [['a']]]), f"test 3 failed: got { sorted([sorted(g) for g in group_anagrams(['a'])])!r } expected { sorted([sorted(g) for g in [['a']]])!r }"
    print(f"all 3 tests passed for group_anagrams")


if __name__ == "__main__":
    _self_test()

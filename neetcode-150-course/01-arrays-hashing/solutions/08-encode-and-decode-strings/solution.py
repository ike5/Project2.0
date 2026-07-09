"""Encode and Decode Strings.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/08-encode-and-decode-strings/solution.py
"""



def encode(strs: list[str]) -> str:
    return ''.join(f"{len(s)}#{s}" for s in strs)


def _self_test() -> None:
    assert encode(['hello', 'world']) == '5#hello5#world', f"test 1 failed: got { encode(['hello', 'world'])!r } expected { '5#hello5#world'!r }"
    assert encode(['', '']) == '0#0#', f"test 2 failed: got { encode(['', ''])!r } expected { '0#0#'!r }"
    assert encode(['a#b', 'c']) == '3#a#b1#c', f"test 3 failed: got { encode(['a#b', 'c'])!r } expected { '3#a#b1#c'!r }"
    print(f"all 3 tests passed for encode")


if __name__ == "__main__":
    _self_test()

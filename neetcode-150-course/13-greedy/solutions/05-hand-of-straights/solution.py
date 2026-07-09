"""Hand of Straights.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/05-hand-of-straights/solution.py
"""



def is_n_straight_hand(hand: list[int], group_size: int) -> bool:
    from collections import Counter
    if len(hand) % group_size: return False
    cnt = Counter(hand)
    for x in sorted(cnt):
        if cnt[x] == 0: continue
        need = cnt[x]
        for i in range(group_size):
            if cnt[x + i] < need:
                return False
            cnt[x + i] -= need
    return True


def _self_test() -> None:
    assert is_n_straight_hand([1, 2, 3, 6, 2, 3, 4, 7, 8], 3) == True, f"test 1 failed: got { is_n_straight_hand([1, 2, 3, 6, 2, 3, 4, 7, 8], 3)!r } expected { True!r }"
    assert is_n_straight_hand([1, 2, 3, 4, 5], 4) == False, f"test 2 failed: got { is_n_straight_hand([1, 2, 3, 4, 5], 4)!r } expected { False!r }"
    print(f"all 2 tests passed for is_n_straight_hand")


if __name__ == "__main__":
    _self_test()

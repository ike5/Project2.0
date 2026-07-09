"""Bitwise AND of Numbers Range.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/08-bitwise-and-of-numbers-range/solution.py
"""



def range_bitwise_and(left: int, right: int) -> int:
    shift = 0
    while left != right:
        left >>= 1
        right >>= 1
        shift += 1
    return left << shift


def _self_test() -> None:
    assert range_bitwise_and(5, 7) == 4, f"test 1 failed: got { range_bitwise_and(5, 7)!r } expected { 4!r }"
    assert range_bitwise_and(0, 0) == 0, f"test 2 failed: got { range_bitwise_and(0, 0)!r } expected { 0!r }"
    assert range_bitwise_and(1, 2147483647) == 0, f"test 3 failed: got { range_bitwise_and(1, 2147483647)!r } expected { 0!r }"
    print(f"all 3 tests passed for range_bitwise_and")


if __name__ == "__main__":
    _self_test()

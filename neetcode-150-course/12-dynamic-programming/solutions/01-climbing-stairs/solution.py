"""Climbing Stairs.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/01-climbing-stairs/solution.py
"""



def climb_stairs(n: int) -> int:
    if n <= 2: return n
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b


def _self_test() -> None:
    assert climb_stairs(2) == 2, f"test 1 failed: got { climb_stairs(2)!r } expected { 2!r }"
    assert climb_stairs(3) == 3, f"test 2 failed: got { climb_stairs(3)!r } expected { 3!r }"
    assert climb_stairs(5) == 8, f"test 3 failed: got { climb_stairs(5)!r } expected { 8!r }"
    print(f"all 3 tests passed for climb_stairs")


if __name__ == "__main__":
    _self_test()

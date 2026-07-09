"""Coin Change II.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/16-coin-change-ii/solution.py
"""



def change(amount: int, coins: list[int]) -> int:
    dp = [0] * (amount + 1)
    dp[0] = 1
    for c in coins:
        for a in range(c, amount + 1):
            dp[a] += dp[a - c]
    return dp[amount]


def _self_test() -> None:
    assert change(5, [1, 2, 5]) == 4, f"test 1 failed: got { change(5, [1, 2, 5])!r } expected { 4!r }"
    assert change(3, [2]) == 0, f"test 2 failed: got { change(3, [2])!r } expected { 0!r }"
    assert change(10, [10]) == 1, f"test 3 failed: got { change(10, [10])!r } expected { 1!r }"
    print(f"all 3 tests passed for change")


if __name__ == "__main__":
    _self_test()

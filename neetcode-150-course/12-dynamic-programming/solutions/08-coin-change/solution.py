"""Coin Change.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/08-coin-change/solution.py
"""



def coin_change(coins: list[int], amount: int) -> int:
    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for c in coins:
        for a in range(c, amount + 1):
            if dp[a - c] + 1 < dp[a]:
                dp[a] = dp[a - c] + 1
    return dp[amount] if dp[amount] != float('inf') else -1


def _self_test() -> None:
    assert coin_change([1, 5, 10, 25], 30) == 2, f"test 1 failed: got { coin_change([1, 5, 10, 25], 30)!r } expected { 2!r }"
    assert coin_change([2], 3) == -1, f"test 2 failed: got { coin_change([2], 3)!r } expected { -1!r }"
    assert coin_change([1], 0) == 0, f"test 3 failed: got { coin_change([1], 0)!r } expected { 0!r }"
    assert coin_change([186, 419, 83, 408], 6249) == 20, f"test 4 failed: got { coin_change([186, 419, 83, 408], 6249)!r } expected { 20!r }"
    print(f"all 4 tests passed for coin_change")


if __name__ == "__main__":
    _self_test()

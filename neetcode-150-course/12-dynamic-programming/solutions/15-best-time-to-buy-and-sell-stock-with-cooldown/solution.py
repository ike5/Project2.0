"""Best Time to Buy and Sell Stock with Cooldown.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/15-best-time-to-buy-and-sell-stock-with-cooldown/solution.py
"""



def max_profit_cooldown(prices: list[int]) -> int:
    n = len(prices)
    if n < 2: return 0
    free = 0
    hold = -prices[0]
    sold = 0
    for i in range(1, n):
        new_free = max(free, sold)
        new_sold = hold + prices[i]
        new_hold = max(hold, free - prices[i])
        free, sold, hold = new_free, new_sold, new_hold
    return max(free, sold)


def _self_test() -> None:
    assert max_profit_cooldown([1, 2, 3, 0, 2]) == 3, f"test 1 failed: got { max_profit_cooldown([1, 2, 3, 0, 2])!r } expected { 3!r }"
    assert max_profit_cooldown([1]) == 0, f"test 2 failed: got { max_profit_cooldown([1])!r } expected { 0!r }"
    print(f"all 2 tests passed for max_profit_cooldown")


if __name__ == "__main__":
    _self_test()

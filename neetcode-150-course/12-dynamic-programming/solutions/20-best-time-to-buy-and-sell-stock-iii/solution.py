"""Best Time to Buy and Sell Stock III.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/20-best-time-to-buy-and-sell-stock-iii/solution.py
"""



def max_profit_two(prices: list[int]) -> int:
    buy1 = sell1 = buy2 = sell2 = float('-inf') if False else 0
    # Use the standard 4-state DP
    buy1 = -prices[0]
    sell1 = 0
    buy2 = -prices[0]
    sell2 = 0
    for i in range(1, len(prices)):
        p = prices[i]
        buy1 = max(buy1, -p)
        sell1 = max(sell1, buy1 + p)
        buy2 = max(buy2, sell1 - p)
        sell2 = max(sell2, buy2 + p)
    return sell2


def _self_test() -> None:
    assert max_profit_two([3, 3, 5, 0, 0, 3, 1, 4]) == 6, f"test 1 failed: got { max_profit_two([3, 3, 5, 0, 0, 3, 1, 4])!r } expected { 6!r }"
    assert max_profit_two([1, 2, 3, 4, 5]) == 4, f"test 2 failed: got { max_profit_two([1, 2, 3, 4, 5])!r } expected { 4!r }"
    print(f"all 2 tests passed for max_profit_two")


if __name__ == "__main__":
    _self_test()

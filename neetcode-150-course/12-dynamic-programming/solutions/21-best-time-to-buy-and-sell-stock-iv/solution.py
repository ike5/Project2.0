"""Best Time to Buy and Sell Stock IV.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/21-best-time-to-buy-and-sell-stock-iv/solution.py
"""



def max_profit_k(k: int, prices: list[int]) -> int:
    n = len(prices)
    if k >= n // 2:
        # unlimited transactions
        s = 0
        for i in range(1, n):
            if prices[i] > prices[i - 1]:
                s += prices[i] - prices[i - 1]
        return s
    # DP with k transactions
    buy = [-float('inf')] * (k + 1)
    sell = [0] * (k + 1)
    for p in prices:
        for j in range(1, k + 1):
            buy[j] = max(buy[j], sell[j - 1] - p)
            sell[j] = max(sell[j], buy[j] + p)
    return sell[k]


def _self_test() -> None:
    assert max_profit_k(2, [2, 4, 1]) == 2, f"test 1 failed: got { max_profit_k(2, [2, 4, 1])!r } expected { 2!r }"
    assert max_profit_k(2, [3, 2, 6, 5, 0, 3]) == 7, f"test 2 failed: got { max_profit_k(2, [3, 2, 6, 5, 0, 3])!r } expected { 7!r }"
    print(f"all 2 tests passed for max_profit_k")


if __name__ == "__main__":
    _self_test()

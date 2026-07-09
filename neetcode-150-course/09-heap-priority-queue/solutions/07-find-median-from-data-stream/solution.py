"""Find Median from Data Stream.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/07-find-median-from-data-stream/solution.py
"""



class MedianFinder:
    def __init__(self) -> None:
        import heapq
        self.small: list[int] = []   # max-heap (negated)
        self.large: list[int] = []   # min-heap

    def add_num(self, num: int) -> None:
        import heapq
        heapq.heappush(self.small, -num)
        # make sure every element in small is <= every element in large
        if self.large and -self.small[0] > self.large[0]:
            heapq.heappush(self.large, -heapq.heappop(self.small))
        # rebalance sizes
        if len(self.small) > len(self.large) + 1:
            heapq.heappush(self.large, -heapq.heappop(self.small))
        elif len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))

    def find_median(self) -> float:
        if len(self.small) > len(self.large):
            return -self.small[0]
        return (-self.small[0] + self.large[0]) / 2.0


def _self_test() -> None:
    pass  # no tests
    print(f"all 0 tests passed for MedianFinder")


if __name__ == "__main__":
    _self_test()

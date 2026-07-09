"""Kth Largest Element in a Stream.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/01-kth-largest-element-in-a-stream/solution.py
"""



class KthLargest:
    def __init__(self, k: int, nums: list[int]) -> None:
        import heapq
        self.k = k
        self.heap: list[int] = []
        for n in nums:
            self.add(n)

    def add(self, val: int) -> int:
        import heapq
        heapq.heappush(self.heap, val)
        if len(self.heap) > self.k:
            heapq.heappop(self.heap)
        return self.heap[0]


def _self_test() -> None:
    pass  # no tests
    print(f"all 0 tests passed for KthLargest")


if __name__ == "__main__":
    _self_test()

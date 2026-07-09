"""LeetCode 362 — Design Hit Counter.

Run me: python 05-observer-pattern/code/hit_counter.py
"""

from collections import deque


class HitCounter:
    def __init__(self) -> None:
        self.queue: deque[int] = deque()

    def hit(self, timestamp: int) -> None:
        self.queue.append(timestamp)

    def getHits(self, timestamp: int) -> int:
        # Drop anything older than (timestamp - 300).
        while self.queue and self.queue[0] <= timestamp - 300:
            self.queue.popleft()
        return len(self.queue)


def main() -> None:
    hc = HitCounter()
    # hits at 1, 2, 3
    hc.hit(1)
    hc.hit(2)
    hc.hit(3)
    print("hits @ t=4   =", hc.getHits(4))    # 3 (all in window)
    hc.hit(300)
    print("hits @ t=300 =", hc.getHits(300))  # 4
    print("hits @ t=301 =", hc.getHits(301))  # 3 (the hit at t=1 fell out)


if __name__ == "__main__":
    main()

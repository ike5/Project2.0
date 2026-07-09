"""Reference solutions for challenge 03."""

from collections import deque


class Hits:
    def __init__(self) -> None:
        self.count = 0

    def record(self) -> None:
        self.count += 1

    def record_n(self, k: int) -> None:
        self.count += k

    def total(self) -> int:
        return self.count

    def reset(self) -> None:
        self.count = 0


class RecentCounter:
    def __init__(self) -> None:
        self.queue: deque[int] = deque()

    def ping(self, t: int) -> int:
        self.queue.append(t)
        while self.queue and self.queue[0] < t - 3000:
            self.queue.popleft()
        return len(self.queue)

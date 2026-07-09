"""Reference solutions for challenge 05."""

from collections import deque
from typing import Callable


class HitCounter:
    def __init__(self) -> None:
        self.queue: deque[int] = deque()

    def hit(self, timestamp: int) -> None:
        self.queue.append(timestamp)

    def getHits(self, timestamp: int) -> int:
        while self.queue and self.queue[0] <= timestamp - 300:
            self.queue.popleft()
        return len(self.queue)


class EventBus:
    def __init__(self) -> None:
        self._subs: dict[str, list[Callable]] = {}

    def on(self, event: str, fn: Callable) -> None:
        self._subs.setdefault(event, []).append(fn)

    def off(self, event: str, fn: Callable) -> None:
        if event in self._subs:
            self._subs[event].remove(fn)

    def emit(self, event: str, *args) -> None:
        for fn in self._subs.get(event, []):
            fn(*args)

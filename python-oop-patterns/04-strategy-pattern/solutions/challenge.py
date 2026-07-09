"""Reference solutions for challenge 04."""

from __future__ import annotations
from typing import Callable


class BrowserHistory:
    def __init__(self, homepage: str) -> None:
        self._back: list[str] = []
        self._current = homepage
        self._forward: list[str] = []

    def visit(self, url: str) -> None:
        self._back.append(self._current)
        self._current = url
        self._forward.clear()

    def back(self, steps: int) -> str:
        while steps > 0 and self._back:
            self._forward.append(self._current)
            self._current = self._back.pop()
            steps -= 1
        return self._current

    def forward(self, steps: int) -> str:
        while steps > 0 and self._forward:
            self._back.append(self._current)
            self._current = self._forward.pop()
            steps -= 1
        return self._current


class Sorter:
    def __init__(self, key: Callable[[str], object]) -> None:
        self.key = key

    def sort(self, xs: list[str]) -> list[str]:
        return sorted(xs, key=self.key)


def identity(x: str) -> str:
    return x


def length(x: str) -> int:
    return len(x)


def last_char(x: str) -> str:
    return x[-1]

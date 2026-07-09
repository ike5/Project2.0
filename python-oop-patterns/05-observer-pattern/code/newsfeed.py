"""Newsfeed with a list of subscribers.

Run me: python 05-observer-pattern/code/newsfeed.py
"""

from __future__ import annotations
from typing import Callable


class Newsfeed:
    def __init__(self) -> None:
        self._subscribers: list[Callable[[str], None]] = []
        self._headlines: list[str] = []

    def subscribe(self, fn: Callable[[str], None]) -> None:
        self._subscribers.append(fn)

    def unsubscribe(self, fn: Callable[[str], None]) -> None:
        self._subscribers.remove(fn)

    def add_headline(self, text: str) -> None:
        self._headlines.append(text)
        for fn in self._subscribers:
            fn(text)


def main() -> None:
    feed = Newsfeed()

    counter = {"n": 0}

    def count_one(_text: str) -> None:
        counter["n"] += 1

    feed.subscribe(print)
    feed.subscribe(lambda h: print(f"  [YELL] {h.upper()}"))
    feed.subscribe(count_one)

    for h in ("first", "second", "third"):
        print(f"\n-- adding: {h!r}")
        feed.add_headline(h)

    print(f"\nfinal count = {counter['n']}")


if __name__ == "__main__":
    main()

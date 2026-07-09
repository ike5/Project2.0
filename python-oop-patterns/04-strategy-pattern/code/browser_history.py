"""LeetCode 1472 — Design Browser History.

Run me: python 04-strategy-pattern/code/browser_history.py
"""


class BrowserHistory:
    def __init__(self, homepage: str) -> None:
        self._back: list[str] = []
        self._current = homepage
        self._forward: list[str] = []

    def visit(self, url: str) -> None:
        self._back.append(self._current)
        self._current = url
        self._forward.clear()              # forward history is gone

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


def main() -> None:
    bh = BrowserHistory("leetcode.com")
    bh.visit("google.com")
    bh.visit("facebook.com")
    bh.visit("youtube.com")
    print(bh.back(1))        # facebook.com
    print(bh.back(1))        # google.com
    print(bh.forward(1))     # facebook.com
    bh.visit("linkedin.com")
    print(bh.forward(2))     # linkedin.com (clamped)
    print(bh.back(2))        # google.com
    print(bh.back(7))        # leetcode.com (clamped)


if __name__ == "__main__":
    main()

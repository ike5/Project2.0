"""Decorator pattern with stackable loggers.

Run me: python 06-decorator-pattern/code/logged.py
"""

from __future__ import annotations
from datetime import datetime


class Logger:
    def log(self, msg: str) -> None:
        print(msg)


class UpperLogger:
    def __init__(self, inner: Logger) -> None:
        self.inner = inner

    def log(self, msg: str) -> None:
        self.inner.log(msg.upper())


class TimestampedLogger:
    def __init__(self, inner: Logger) -> None:
        self.inner = inner

    def log(self, msg: str) -> None:
        self.inner.log(f"[{datetime.now():%H:%M:%S}] {msg}")


def main() -> None:
    log = TimestampedLogger(UpperLogger(Logger()))
    log.log("hi")
    log.log("module ready")


if __name__ == "__main__":
    main()

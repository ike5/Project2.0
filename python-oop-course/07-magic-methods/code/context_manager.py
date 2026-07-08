"""Two context managers: a class-based Timer and a @contextmanager one.

Run:
    python 07-magic-methods/code/context_manager.py
"""

import time
from contextlib import contextmanager


class Timer:
    def __enter__(self):
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.elapsed = time.perf_counter() - self._t0
        print(f"Timer (class):  elapsed = {self.elapsed:.4f}s")
        return False                           # propagate exceptions


@contextmanager
def timer():
    t0 = time.perf_counter()
    yield
    print(f"Timer (decorator): elapsed = {time.perf_counter() - t0:.4f}s")


def main() -> None:
    with Timer():
        total = sum(range(1, 100_000))
    print("sum =", total)

    with timer():
        total = sum(range(1, 100_000))
    print("sum =", total)


if __name__ == "__main__":
    main()

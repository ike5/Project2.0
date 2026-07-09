"""Smoke test — confirm Python is ready for the course."""

import sys


def main() -> int:
    if sys.version_info < (3, 10):
        print(f"FAIL: need Python 3.10+, got {sys.version}")
        return 1

    # A tiny dict-as-map demo to prove the basic building block works.
    counts: dict[str, int] = {}
    for ch in "abracadabra":
        counts[ch] = counts.get(ch, 0) + 1

    expected = {"a": 5, "b": 2, "r": 2, "c": 1, "d": 1}
    if counts != expected:
        print(f"FAIL: counts = {counts}, expected {expected}")
        return 1

    print("OK: Python is ready for LeetCode.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

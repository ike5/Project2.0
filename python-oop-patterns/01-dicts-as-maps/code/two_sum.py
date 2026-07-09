"""Compare brute force vs. hash-map solutions to Two Sum.

Run me: python 01-dicts-as-maps/code/two_sum.py
"""

import time
from typing import Optional


def two_sum_brute(nums: list[int], target: int) -> Optional[tuple[int, int]]:
    n = len(nums)
    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] + nums[j] == target:
                return (i, j)
    return None


def two_sum_hash(nums: list[int], target: int) -> Optional[tuple[int, int]]:
    seen: dict[int, int] = {}              # value -> index
    for i, x in enumerate(nums):
        need = target - x
        if need in seen:
            return (seen[need], i)
        seen[x] = i
    return None


def benchmark(label: str, fn, nums, target, n_runs: int = 3) -> tuple[any, float]:
    best = float("inf")
    result = None
    for _ in range(n_runs):
        t0 = time.perf_counter()
        result = fn(nums, target)
        best = min(best, time.perf_counter() - t0)
    print(f"{label:6s}: {result}   in {best:.6f} s")
    return result, best


def main() -> None:
    NS = (100, 1_000, 10_000)

    for n in NS:
        nums = list(range(n))                  # worst case: 0..n-1
        target = (n - 1) + (n - 2)             # the largest two add up

        print(f"\n--- n = {n} ---")
        if n <= 10_000:
            r1, t1 = benchmark("brute", two_sum_brute, nums, target)
        else:
            print("brute: skipped (would take too long)")
            t1 = float("inf")
            r1 = None
        r2, t2 = benchmark("hash", two_sum_hash, nums, target)

        if t1 != float("inf"):
            print(f"hash is {t1 / t2:.0f}x faster on n={n}")

        assert r1 == r2 or r1 is None and r2 is None, "mismatch!"

    print("\nAll solutions agree.")


if __name__ == "__main__":
    main()

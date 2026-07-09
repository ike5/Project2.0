"""pytest tests for the dict-based Two Sum."""

import pathlib
import sys

# Make the lab script importable.
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from two_sum import two_sum_brute, two_sum_hash


def test_basic():
    assert two_sum_hash([2, 7, 11, 15], 9) == (0, 1)


def test_unsorted():
    assert two_sum_hash([3, 2, 4], 6) == (1, 2)


def test_duplicates():
    assert two_sum_hash([3, 3], 6) == (0, 1)


def test_no_solution():
    assert two_sum_hash([1, 2, 3], 7) is None


def test_brute_matches_hash():
    # For a given target, multiple valid pairs may exist. Each solution should
    # return *some* valid pair, or None if no pair exists. We just check that
    # each solution's pair is valid and that they agree on "no solution" cases.
    nums = list(range(20))
    for target in range(0, 38):
        for solution in (two_sum_brute, two_sum_hash):
            pair = solution(nums, target)
            if pair is None:
                # If this solution says none, the other should too.
                other = (two_sum_hash if solution is two_sum_brute else two_sum_brute)
                assert other(nums, target) is None
            else:
                i, j = pair
                assert 0 <= i < j < len(nums)
                assert nums[i] + nums[j] == target

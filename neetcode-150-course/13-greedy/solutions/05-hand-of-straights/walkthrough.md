# Hand of Straights - walkthrough

**Difficulty:** Medium &middot; **Module:** 13 Greedy

## Brief

Alice has some number of cards and she wants to rearrange the cards into groups so that each group is of size `groupSize` and consists of `groupSize` consecutive cards. Given an integer array `hand` where `hand[i]` is the value written on the ith card and an integer `groupSize`, return `True` if she can rearrange the cards, or `False` otherwise.

## Examples

- `hand = [1,2,3,6,2,3,4,7,8], groupSize = 3` &rarr; `True`
- `hand = [1,2,3,4,5], groupSize = 4` &rarr; `False`

## Constraints

- 1 <= hand.length <= 10^4
- 0 <= hand[i] <= 10^9
- 1 <= groupSize <= hand.length

## Intuition

Greedy. Always try to form a group starting at the smallest
ungrouped card. If we can't, fail.

The Java version uses a count map and decrements instead of mutating
the array.

**Time:** O(n · groupSize). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

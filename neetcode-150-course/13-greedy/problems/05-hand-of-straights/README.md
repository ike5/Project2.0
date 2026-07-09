# Hand of Straights

**Difficulty:** Medium

## Problem

Alice has some number of cards and she wants to rearrange the cards into groups so that each group is of size `groupSize` and consists of `groupSize` consecutive cards. Given an integer array `hand` where `hand[i]` is the value written on the ith card and an integer `groupSize`, return `True` if she can rearrange the cards, or `False` otherwise.

## Examples

```
Input:  hand = [1,2,3,6,2,3,4,7,8], groupSize = 3
Output: True
```

```
Input:  hand = [1,2,3,4,5], groupSize = 4
Output: False
```

## Constraints

- 1 <= hand.length <= 10^4
- 0 <= hand[i] <= 10^9
- 1 <= groupSize <= hand.length

## Hints

1. Sort the hand. For each smallest ungrouped card, try to form a group starting there.

## Solution

See [`../../solutions/05-hand-of-straights/`](../../solutions/05-hand-of-straights/) for the Python and Java 21 solutions and a step-by-step walkthrough.

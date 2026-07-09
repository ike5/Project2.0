# House Robber III - walkthrough

**Difficulty:** Medium &middot; **Module:** 07 Trees

## Brief

The thief has found himself a new place for his thievery again. There is only one entrance to this area, called `root`. Besides the `root`, each house has one and only one parent house. After a tour, the smart thief realized that all houses in this place form a binary tree. It will automatically contact the police if two directly-linked houses were broken into on the same night. Determine the maximum amount of money the thief can rob tonight without alerting the police.

## Examples

- `root = [3,2,3,null,3,null,1]` &rarr; `7`
- `root = [3,4,5,1,3,null,1]` &rarr; `9`

## Constraints

- 0 <= number of nodes <= 10^4
- 0 <= Node.val <= 10^4

## Intuition

Each subtree returns `(rob, skip)`. Combining:
- `rob = val + skip(left) + skip(right)`
- `skip = max(rob, skip)(left) + max(rob, skip)(right)`

**Time:** O(n). **Space:** O(h).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

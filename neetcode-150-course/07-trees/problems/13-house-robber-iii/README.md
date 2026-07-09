# House Robber III

**Difficulty:** Medium

## Problem

The thief has found himself a new place for his thievery again. There is only one entrance to this area, called `root`. Besides the `root`, each house has one and only one parent house. After a tour, the smart thief realized that all houses in this place form a binary tree. It will automatically contact the police if two directly-linked houses were broken into on the same night. Determine the maximum amount of money the thief can rob tonight without alerting the police.

## Examples

```
Input:  root = [3,2,3,null,3,null,1]
Output: 7
```

```
Input:  root = [3,4,5,1,3,null,1]
Output: 9
```

## Constraints

- 0 <= number of nodes <= 10^4
- 0 <= Node.val <= 10^4

## Hints

1. For each node, return `(rob, skip)` — the best if we rob or skip this node.
2. If we rob, we add val + skip(left) + skip(right). If we skip, we take max(rob or skip) of each child.

## Solution

See [`../../solutions/13-house-robber-iii/`](../../solutions/13-house-robber-iii/) for the Python and Java 21 solutions and a step-by-step walkthrough.

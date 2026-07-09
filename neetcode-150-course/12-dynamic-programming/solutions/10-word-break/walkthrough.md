# Word Break - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

Given a string `s` and a dictionary of strings `wordDict`, return `True` if `s` can be segmented into a space-separated sequence of one or more dictionary words.

## Examples

- `s = 'leetcode', wordDict = ['leet','code']` &rarr; `True`
- `s = 'applepenapple', wordDict = ['apple','pen']` &rarr; `True`
- `s = 'catsandog', wordDict = ['cats','dog','sand','and','cat']` &rarr; `False`

## Constraints

- 1 <= len(s) <= 300
- 1 <= wordDict.length <= 1000
- 1 <= wordDict[i].length <= 20
- s and wordDict[i] consist of only lowercase English letters

## Intuition

Bottom-up DP. `dp[i]` = can segment `s[:i]`. For each `i`, try
each `j < i` and check if `s[j:i]` is in the dict.

**Time:** O(n² · L) where L is the average word length. **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

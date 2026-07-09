# Design Twitter

**Difficulty:** Medium

## Problem

Design a simplified version of Twitter where users can post tweets, follow / unfollow another user, and see the 10 most recent tweet IDs in the user's news feed. Implement the `Twitter` class.

## Examples

```
Input:  postTweet(1, 5); getNewsFeed(1) -> [5]; follow(1, 2); postTweet(2, 6); getNewsFeed(1) -> [6, 5]; unfollow(1, 2); getNewsFeed(1) -> [5]
Output: [5], [6, 5], [5]
```

## Constraints

- 1 <= userId, followerId, followeeId <= 500
- 0 <= tweetId <= 10^4
- At most 3 * 10^4 calls total

## Hints

1. Each user has a list of their own tweets (with timestamps).
2. News feed: merge the most recent tweets of the user and followees using a heap of size 10.

## Solution

See [`../../solutions/06-design-twitter/`](../../solutions/06-design-twitter/) for the Python and Java 21 solutions and a step-by-step walkthrough.

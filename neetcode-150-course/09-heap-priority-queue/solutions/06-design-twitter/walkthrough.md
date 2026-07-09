# Design Twitter - walkthrough

**Difficulty:** Medium &middot; **Module:** 09 Heap Priority Queue

## Brief

Design a simplified version of Twitter where users can post tweets, follow / unfollow another user, and see the 10 most recent tweet IDs in the user's news feed. Implement the `Twitter` class.

## Examples

- `postTweet(1, 5); getNewsFeed(1) -> [5]; follow(1, 2); postTweet(2, 6); getNewsFeed(1) -> [6, 5]; unfollow(1, 2); getNewsFeed(1) -> [5]` &rarr; `[5], [6, 5], [5]`

## Constraints

- 1 <= userId, followerId, followeeId <= 500
- 0 <= tweetId <= 10^4
- At most 3 * 10^4 calls total

## Intuition

Each user has a list of `(time, tweet_id)` pairs (newest last).
The news feed is the 10 most recent tweets from the user and their
followees. Use a **max-heap on timestamp** with lazy next-tweet fetch
(merge k sorted lists).

**Time:** getNewsFeed O(F log F) where F is the number of followees.
**Space:** O(U + T).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

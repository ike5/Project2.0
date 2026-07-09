"""LeetCode 355 — Design Twitter, with a Tweet dataclass.

Run me: python 11-composition/code/twitter.py
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class Tweet:
    id: int
    user_id: int
    ts: int


class Twitter:
    def __init__(self) -> None:
        self._tweets: dict[int, deque[Tweet]] = defaultdict(deque)
        self._following: dict[int, set[int]] = defaultdict(set)
        self._clock = 0

    def postTweet(self, userId: int, tweetId: int) -> None:
        self._clock += 1
        # Newest at the left so we can iterate newest-first cheaply.
        self._tweets[userId].appendleft(Tweet(id=tweetId, user_id=userId, ts=self._clock))

    def getNewsFeed(self, userId: int) -> list[int]:
        relevant = {userId} | self._following[userId]
        tweets: list[Tweet] = []
        for uid in relevant:
            tweets.extend(self._tweets[uid])
        # Sort by timestamp descending so the most recent tweets come first.
        tweets.sort(key=lambda t: t.ts, reverse=True)
        return [t.id for t in tweets[:10]]

    def follow(self, followerId: int, followeeId: int) -> None:
        if followerId != followeeId:
            self._following[followerId].add(followeeId)

    def unfollow(self, followerId: int, followeeId: int) -> None:
        self._following[followerId].discard(followeeId)


def main() -> None:
    tw = Twitter()

    tw.postTweet(1, 5)
    tw.postTweet(1, 10)
    tw.postTweet(1, 15)
    tw.postTweet(2, 20)
    tw.postTweet(2, 25)

    print("user 1 feed (no follows) =", tw.getNewsFeed(1))
    tw.follow(1, 2)
    print("user 1 feed (after follow 2) =", tw.getNewsFeed(1))
    tw.unfollow(1, 2)
    print("user 1 feed (after unfollow 2) =", tw.getNewsFeed(1))


if __name__ == "__main__":
    main()

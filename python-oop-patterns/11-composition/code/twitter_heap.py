"""A heap-merge version of getNewsFeed.

Run me: python 11-composition/code/twitter_heap.py
"""

import heapq
from collections import defaultdict, deque
from dataclasses import dataclass


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
        self._tweets[userId].appendleft(Tweet(id=tweetId, user_id=userId, ts=self._clock))

    def getNewsFeed(self, userId: int) -> list[int]:
        relevant = {userId} | self._following[userId]
        # Each user's stream is already sorted newest-first. heapq.merge keeps the
        # top 10 in a heap of size O(|relevant|).
        merged = heapq.merge(*(self._tweets[u] for u in relevant), key=lambda t: -t.ts)
        return [t.id for _, t in zip(range(10), merged)]

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
    tw.follow(1, 2)
    print("user 1 feed (heap-merge) =", tw.getNewsFeed(1))


if __name__ == "__main__":
    main()

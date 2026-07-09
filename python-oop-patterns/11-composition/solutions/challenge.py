"""Reference solutions for challenge 11."""

from collections import defaultdict, deque
import time
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
        tweets = []
        for uid in relevant:
            tweets.extend(self._tweets[uid])
        tweets.sort(key=lambda t: t.ts, reverse=True)
        return [t.id for t in tweets[:10]]

    def follow(self, followerId: int, followeeId: int) -> None:
        if followerId != followeeId:
            self._following[followerId].add(followeeId)

    def unfollow(self, followerId: int, followeeId: int) -> None:
        self._following[followerId].discard(followeeId)


class RateLimiter:
    def __init__(self, n: int, window_seconds: float) -> None:
        self.n = n
        self.window = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str = "default") -> bool:
        now = time.monotonic()
        dq = self._events[key]
        while dq and now - dq[0] > self.window:
            dq.popleft()
        if len(dq) >= self.n:
            return False
        dq.append(now)
        return True

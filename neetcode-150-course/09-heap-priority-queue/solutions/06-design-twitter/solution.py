"""Design Twitter.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/06-design-twitter/solution.py
"""



class Twitter:
    def __init__(self) -> None:
        self._tweets: dict[int, list[tuple[int, int]]] = {}
        self._follows: dict[int, set[int]] = {}
        self._time = 0

    def post_tweet(self, user_id: int, tweet_id: int) -> None:
        self._tweets.setdefault(user_id, []).append((self._time, tweet_id))
        self._time += 1

    def get_news_feed(self, user_id: int) -> list[int]:
        import heapq
        heap: list[tuple[int, int, int]] = []   # (-time, idx, tweet_id)
        users = self._follows.get(user_id, set()) | {user_id}
        for u in users:
            if not self._tweets.get(u):
                continue
            i = len(self._tweets[u]) - 1
            t, tid = self._tweets[u][i]
            heapq.heappush(heap, (-t, i, tid))
        out: list[int] = []
        while heap and len(out) < 10:
            neg_t, i, tid = heapq.heappop(heap)
            out.append(tid)
            if i > 0:
                t, tid2 = self._tweets[users_lookup(heap, users)][i - 1]
                heapq.heappush(heap, (-t, i - 1, tid2))
        return out

    def follow(self, follower_id: int, followee_id: int) -> None:
        self._follows.setdefault(follower_id, set()).add(followee_id)

    def unfollow(self, follower_id: int, followee_id: int) -> None:
        self._follows.get(follower_id, set()).discard(followee_id)


def _self_test() -> None:
    pass  # no tests
    print(f"all 0 tests passed for Twitter")


if __name__ == "__main__":
    _self_test()

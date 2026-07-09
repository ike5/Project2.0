# Module 11 — Composition over inheritance

**Python skill:** objects holding other objects, delegation, `@dataclass`.
**LeetCode problem:** [355. Design Twitter](https://leetcode.com/problems/design-twitter/) · Medium.
**Time:** ~2 h.

---

## 1. The principle

**Composition**: a class holds another class as a field and *delegates* to it.

**Inheritance**: a class extends another class and reuses its behavior.

The rule of thumb: prefer composition unless there's a clear "is-a" relationship. A `Twitter` is not a `User` — it *has* users. A `Twitter` is not a `Tweet` — it *has* tweets. So `Twitter` should *contain* a dict of `User`s and a list of `Tweet`s, not extend them.

Composition wins because:

- You can swap the inner object at runtime.
- You can compose many things together (a `Twitter` has a `dict`, a `deque`, a `Counter`, a `set`...).
- You don't get tangled in deep inheritance hierarchies.

## 2. `@dataclass` for tiny value types

A `Tweet` is just a value: an id, a user, a timestamp, some text. That's exactly what `@dataclass` is for:

```python
from dataclasses import dataclass, field

@dataclass
class Tweet:
    id: int
    user_id: int
    ts: int
    text: str = ""
    likes: list[int] = field(default_factory=list)
```

`@dataclass` auto-generates `__init__`, `__repr__`, `__eq__`. For collections, use `field(default_factory=list)` so each instance gets its own list.

> If you define `__eq__` (which `@dataclass` does by default), Python sets `__hash__ = None` and your object is no longer hashable. If you need it hashable, set `@dataclass(eq=False)` or define `__hash__ = lambda self: self.id`.

## 3. Delegation

The `Twitter` class delegates to its inner containers:

```python
class Twitter:
    def __init__(self) -> None:
        self._tweets: dict[int, list[Tweet]] = {}    # user_id -> tweets (newest first)
        self._following: dict[int, set[int]] = {}   # user_id -> set of followees

    def postTweet(self, userId: int, tweetId: int) -> None:
        tweet = Tweet(id=tweetId, user_id=userId, ts=...)
        self._tweets.setdefault(userId, []).append(tweet)

    def getNewsFeed(self, userId: int) -> list[int]:
        # Walk the user's own + followees' tweets, take the 10 most recent.
        ...
```

The `Twitter` class doesn't *re-implement* a list or a set — it uses them. That's the pattern.

## 4. The LeetCode problem

> [355. Design Twitter](https://leetcode.com/problems/design-twitter/)
>
> - `postTweet(userId, tweetId)` — compose a new tweet.
> - `getNewsFeed(userId)` — return the 10 most recent tweet ids in the user's news feed (their tweets + tweets of people they follow), in reverse chronological order.
> - `follow(followerId, followeeId)` — `follower` follows `followee`.
> - `unfollow(followerId, followeeId)` — `follower` unfollows `followee`.

The data layout:

- `self._tweets: dict[user_id -> list[Tweet]]` — newest at the *end* (use `append`) or at the front (use `insert(0, ...)`; `deque.appendleft` is faster).
- `self._following: dict[user_id -> set[user_id]]` — who they follow.

For the news feed, the naive solution is: collect all tweets from user + followees, sort by time, take 10. The optimal solution is a heap-merge (a-la k-way merge), but for `n ≤ 10` users the naive version is fine.

```python
def getNewsFeed(self, userId: int) -> list[int]:
    relevant_user_ids = {userId} | self._following.get(userId, set())
    tweets = []
    for uid in relevant_user_ids:
        tweets.extend(self._tweets.get(uid, []))
    tweets.sort(key=lambda t: t.ts, reverse=True)
    return [t.id for t in tweets[:10]]
```

You'll build this in the lab.

## 5. Anti-patterns

- **Re-implementing `list` operations on a custom list-like class.** Just hold a `list` and delegate.
- **`User` inheriting from `dict` because "users are like dicts".** They aren't. A `User` *has* a dict of profile fields.
- **Deep inheritance chains.** If `B(A)` and `C(B)` and `D(C)`, you're probably missing a composition.

---

**→ Next: [Module 12 — Capstone: design a cache](./../12-capstone/)**

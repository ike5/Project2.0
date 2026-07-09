# Lab 11 — Composition

**You'll:** build a `Tweet` dataclass and a `Twitter` class, then add a `getNewsFeed` that uses a heap-merge for the optimal version. ⏱️ ~40 min.

---

## Part A — Tweet and Twitter

```bash
python 11-composition/code/twitter.py
```

✅ You should see:

- 3 tweets posted by user 1, 2 by user 2.
- User 1's news feed = user 1's 3 + user 2's 2, sorted by ts descending, top 10.
- After user 1 follows user 2, the feed is unchanged (already included).
- After user 1 unfollows user 2, the feed is just user 1's tweets.

Read the implementation. Note the `_tweets` and `_following` dicts — the class composes them rather than inheriting.

## Part B — Add a heap-merge

Open `11-composition/code/twitter_heap.py`. There's a `get_news_feed_heap` function that uses `heapq.merge` to merge pre-sorted streams. Run the demo and confirm it gives the same answer as the sort version.

## Part C — pytest

```bash
python -m pytest 11-composition/code/test_twitter.py
```

✅ All tests pass.

---

When everything passes, move to the challenge.

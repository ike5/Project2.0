"""pytest tests for Twitter."""

from twitter import Twitter


def test_post_and_get_own():
    tw = Twitter()
    tw.postTweet(1, 5)
    assert tw.getNewsFeed(1) == [5]


def test_follow_unfollow():
    tw = Twitter()
    tw.postTweet(1, 5)
    tw.postTweet(2, 6)
    tw.follow(1, 2)
    assert tw.getNewsFeed(1) == [6, 5]
    tw.unfollow(1, 2)
    assert tw.getNewsFeed(1) == [5]


def test_self_follow_is_noop():
    tw = Twitter()
    tw.postTweet(1, 5)
    tw.follow(1, 1)
    assert tw.getNewsFeed(1) == [5]


def test_top_10():
    tw = Twitter()
    for i in range(20):
        tw.postTweet(1, i)
    assert tw.getNewsFeed(1) == list(reversed(range(10, 20)))

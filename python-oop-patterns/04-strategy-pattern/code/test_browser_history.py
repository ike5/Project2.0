"""pytest tests for BrowserHistory."""

from browser_history import BrowserHistory


def test_basic_example():
    bh = BrowserHistory("leetcode.com")
    bh.visit("google.com")
    bh.visit("facebook.com")
    bh.visit("youtube.com")
    assert bh.back(1) == "facebook.com"
    assert bh.back(1) == "google.com"
    assert bh.forward(1) == "facebook.com"
    bh.visit("linkedin.com")
    assert bh.forward(2) == "linkedin.com"     # forward history was cleared
    assert bh.back(2) == "google.com"
    assert bh.back(7) == "leetcode.com"         # clamped


def test_visit_clears_forward():
    bh = BrowserHistory("a.com")
    bh.visit("b.com")
    bh.visit("c.com")
    bh.back(1)
    bh.visit("d.com")
    assert bh.forward(1) == "d.com"            # can't go forward

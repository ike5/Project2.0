"""pytest tests for HitCounter."""

from hit_counter import HitCounter


def test_basic():
    hc = HitCounter()
    hc.hit(1)
    hc.hit(2)
    hc.hit(3)
    assert hc.getHits(4) == 3


def test_expiry():
    hc = HitCounter()
    hc.hit(1)
    hc.hit(2)
    hc.hit(3)
    hc.hit(300)
    assert hc.getHits(300) == 4
    # t=301 -> window is [2, 301], so t=1 falls out
    assert hc.getHits(301) == 3


def test_empty():
    hc = HitCounter()
    assert hc.getHits(1) == 0

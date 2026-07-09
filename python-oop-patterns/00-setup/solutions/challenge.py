"""Reference solution for challenge 00.

You should have:

1. Verified your environment with VERIFY.md.
2. Added a new demo function to containers_tour.py (or a separate file).
3. Written a pytest test using pytest.approx.
"""


def my_first_test() -> None:
    import pytest

    # Floating point comparison — exact equality would fail.
    assert 0.1 + 0.2 == pytest.approx(0.3)


if __name__ == "__main__":
    my_first_test()
    print("OK: 0.1 + 0.2 == 0.3 (with pytest.approx)")

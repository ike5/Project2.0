"""Tests for Loan."""

from datetime import date, timedelta

from library.loan import Loan


def test_new_loan_is_open():
    from datetime import timedelta
    today = date.today()
    ln = Loan("m1", "isbn1", today, today + timedelta(days=14))
    assert ln.is_open is True
    assert ln.is_overdue is False


def test_loan_with_returned_on_is_closed():
    ln = Loan("m1", "isbn1", date(2026, 1, 1), date(2026, 1, 15), returned_on=date(2026, 1, 10))
    assert ln.is_open is False


def test_overdue_loan_with_past_due():
    ln = Loan("m1", "isbn1", date(2020, 1, 1), date(2020, 1, 15))   # due in the past
    assert ln.is_overdue is True


def test_loan_equality_and_hash():
    a = Loan("m1", "isbn1", date(2026, 1, 1), date(2026, 1, 15))
    b = Loan("m1", "isbn1", date(2026, 1, 1), date(2026, 1, 15))
    assert a == b
    assert hash(a) == hash(b)
    assert {a, b} == {a}                        # duplicates collapse


def test_loan_is_immutable():
    ln = Loan("m1", "isbn1", date(2026, 1, 1), date(2026, 1, 15))
    try:
        ln.returned_on = date(2026, 1, 10)     # type: ignore
    except Exception as e:
        assert "FrozenInstanceError" in type(e).__name__ or "frozen" in str(e).lower()
    else:
        raise AssertionError("expected mutation to fail")

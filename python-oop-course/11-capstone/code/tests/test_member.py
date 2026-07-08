"""Tests for Member."""

import pytest
from datetime import date, timedelta

from library.loan import Loan
from library.member import Member


def test_create_member_stores_fields():
    m = Member("m1", "Ana")
    assert m.member_id == "m1"
    assert m.name == "Ana"
    assert m.active_loans == []
    assert m.loans == []


def test_add_loan_makes_it_active():
    m = Member("m1", "Ana")
    loan = Loan("m1", "isbn1", date.today(), date.today() + timedelta(days=14))
    m._add_loan(loan)
    assert m.loans == [loan]
    assert m.active_loans == [loan]


def test_replace_loan_swaps_in_new_loan():
    m = Member("m1", "Ana")
    open_loan = Loan("m1", "isbn1", date.today(), date.today() + timedelta(days=14))
    returned = Loan("m1", "isbn1", open_loan.borrowed_on, open_loan.due_on, returned_on=date.today())
    m._add_loan(open_loan)
    m._replace_loan(open_loan, returned)
    assert m.active_loans == []
    assert m.loans == [returned]


def test_active_loans_excludes_returned():
    m = Member("m1", "Ana")
    open_loan = Loan("m1", "isbn1", date.today(), date.today() + timedelta(days=14))
    closed_loan = Loan("m1", "isbn2", date.today(), date.today() + timedelta(days=14), returned_on=date.today())
    m._add_loan(open_loan)
    m._add_loan(closed_loan)
    assert m.active_loans == [open_loan]
    assert m.loans == [open_loan, closed_loan]


@pytest.mark.parametrize("kwargs", [
    {"member_id": ""},
    {"name": ""},
])
def test_invalid_construction(kwargs):
    base = {"member_id": "m1", "name": "Ana"}
    base.update(kwargs)
    with pytest.raises(ValueError):
        Member(**base)

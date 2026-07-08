"""Tests for the Library orchestrator."""

import pytest

from library import Book, Library, Member
from library.errors import (
    BookNotFound,
    LoanNotFound,
    MemberNotFound,
    NoCopiesAvailable,
)


@pytest.fixture
def lib():
    lib = Library("Test")
    lib.add_book(Book("A", "X", "1", copies=2))
    lib.add_book(Book("B", "Y", "2", copies=1))
    lib.add_member(Member("m1", "Ana"))
    return lib


def test_add_book(lib):
    assert len(lib.books) == 2


def test_duplicate_book_raises(lib):
    with pytest.raises(ValueError):
        lib.add_book(Book("Dup", "X", "1", copies=1))


def test_add_member(lib):
    assert len(lib.members) == 1


def test_duplicate_member_raises(lib):
    with pytest.raises(ValueError):
        lib.add_member(Member("m1", "Other"))


def test_find_book_returns_book(lib):
    assert lib.find_book("1").title == "A"


def test_find_book_missing_raises(lib):
    with pytest.raises(BookNotFound):
        lib.find_book("nope")


def test_find_member_missing_raises(lib):
    with pytest.raises(MemberNotFound):
        lib.find_member("nope")


def test_borrow_creates_loan_and_decrements_available(lib):
    loan = lib.borrow("m1", "2")
    assert lib.find_book("2").available == 0
    assert loan.member_id == "m1"
    assert loan.book_isbn == "2"
    assert loan.is_open
    assert len(lib.find_member("m1").active_loans) == 1


def test_borrow_last_copy_then_blocked(lib):
    lib.borrow("m1", "2")
    with pytest.raises(NoCopiesAvailable):
        lib.borrow("m1", "2")


def test_return_reopens_availability(lib):
    lib.borrow("m1", "2")
    lib.return_book("m1", "2")
    assert lib.find_book("2").available == 1
    assert lib.find_member("m1").active_loans == []


def test_return_without_open_loan_raises(lib):
    with pytest.raises(LoanNotFound):
        lib.return_book("m1", "2")


def test_return_unknown_member_raises(lib):
    with pytest.raises(MemberNotFound):
        lib.return_book("nope", "2")


def test_return_unknown_book_raises(lib):
    lib.borrow("m1", "2")
    with pytest.raises(BookNotFound):
        lib.return_book("m1", "nope")


def test_borrow_then_return_then_borrow_again(lib):
    lib.borrow("m1", "2")
    lib.return_book("m1", "2")
    lib.borrow("m1", "2")
    assert lib.find_book("2").available == 0
    assert len(lib.find_member("m1").active_loans) == 1

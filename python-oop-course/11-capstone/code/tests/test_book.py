"""Tests for Book."""

import pytest

from library.book import Book
from library.errors import NoCopiesAvailable


def test_create_book_stores_fields():
    b = Book("Clean Code", "Robert C. Martin", "978-0-13-235088-4", copies=2)
    assert b.title == "Clean Code"
    assert b.author == "Robert C. Martin"
    assert b.isbn == "978-0-13-235088-4"
    assert b.total == 2
    assert b.available == 2
    assert b.is_available is True


def test_take_one_decrements_available():
    b = Book("X", "Y", "1", copies=1)
    b._take_one()
    assert b.available == 0
    assert b.is_available is False


def test_take_one_with_no_copies_raises():
    b = Book("X", "Y", "1", copies=1)
    b._take_one()
    with pytest.raises(NoCopiesAvailable):
        b._take_one()


def test_return_one_increments_available():
    b = Book("X", "Y", "1", copies=1)
    b._take_one()
    b._return_one()
    assert b.available == 1


def test_return_one_at_total_raises():
    b = Book("X", "Y", "1", copies=1)
    with pytest.raises(ValueError):
        b._return_one()


@pytest.mark.parametrize("kwargs", [
    {"title": ""},
    {"author": ""},
    {"isbn": ""},
    {"copies": 0},
    {"copies": -1},
])
def test_invalid_construction(kwargs):
    base = {"title": "X", "author": "Y", "isbn": "1", "copies": 1}
    base.update(kwargs)
    with pytest.raises(ValueError):
        Book(**base)


def test_repr_contains_title_and_isbn():
    b = Book("Clean Code", "Robert C. Martin", "978-0-13-235088-4")
    r = repr(b)
    assert "Clean Code" in r
    assert "978-0-13-235088-4" in r

"""The Library: a container of books and members, with a borrow/return workflow."""

from datetime import date, timedelta

from library.book import Book
from library.errors import BookNotFound, LoanNotFound, MemberNotFound
from library.loan import Loan
from library.member import Member


DEFAULT_LOAN_DAYS = 14


class Library:
    def __init__(self, name: str = "Neighborhood Library") -> None:
        self.name = name
        self._books: dict[str, Book] = {}        # isbn -> Book
        self._members: dict[str, Member] = {}    # member_id -> Member
        self._loans: list[Loan] = []

    # -- collection management ------------------------------------------------

    def add_book(self, book: Book) -> None:
        if book.isbn in self._books:
            raise ValueError(f"book with isbn {book.isbn!r} already in library")
        self._books[book.isbn] = book

    def add_member(self, member: Member) -> None:
        if member.member_id in self._members:
            raise ValueError(f"member with id {member.member_id!r} already registered")
        self._members[member.member_id] = member

    @property
    def books(self) -> list[Book]:
        return list(self._books.values())

    @property
    def members(self) -> list[Member]:
        return list(self._members.values())

    @property
    def loans(self) -> list[Loan]:
        return list(self._loans)

    # -- lookups -------------------------------------------------------------

    def find_book(self, isbn: str) -> Book:
        try:
            return self._books[isbn]
        except KeyError:
            raise BookNotFound(f"no book with isbn {isbn!r}")

    def find_member(self, member_id: str) -> Member:
        try:
            return self._members[member_id]
        except KeyError:
            raise MemberNotFound(f"no member with id {member_id!r}")

    # -- workflows -----------------------------------------------------------

    def borrow(self, member_id: str, isbn: str, *, days: int = DEFAULT_LOAN_DAYS) -> Loan:
        member = self.find_member(member_id)
        book = self.find_book(isbn)
        book._take_one()
        loan = Loan(
            member_id=member.member_id,
            book_isbn=book.isbn,
            borrowed_on=date.today(),
            due_on=date.today() + timedelta(days=days),
        )
        self._loans.append(loan)
        member._add_loan(loan)
        return loan

    def return_book(self, member_id: str, isbn: str) -> Loan:
        member = self.find_member(member_id)
        book = self.find_book(isbn)
        open_loan = next(
            (ln for ln in member.active_loans if ln.book_isbn == isbn),
            None,
        )
        if open_loan is None:
            raise LoanNotFound(f"member {member_id!r} has no open loan for {isbn!r}")
        book._return_one()
        new_loan = Loan(
            member_id=open_loan.member_id,
            book_isbn=open_loan.book_isbn,
            borrowed_on=open_loan.borrowed_on,
            due_on=open_loan.due_on,
            returned_on=date.today(),
        )
        idx = self._loans.index(open_loan)
        self._loans[idx] = new_loan
        member._replace_loan(open_loan, new_loan)
        return new_loan

    def __repr__(self) -> str:
        return f"Library({self.name!r}, {len(self._books)} books, {len(self._members)} members, {len(self._loans)} loans)"

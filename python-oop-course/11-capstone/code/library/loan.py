"""A Loan: a record that a Member borrowed a Book on a date, due back on a date.

Loans are immutable. To "return" a book, the Library creates a new Loan with
returned_at set, replacing the open one.
"""

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class Loan:
    member_id: str
    book_isbn: str
    borrowed_on: date
    due_on: date
    returned_on: date | None = None

    @property
    def is_open(self) -> bool:
        return self.returned_on is None

    @property
    def is_overdue(self) -> bool:
        return self.is_open and self.due_on < date.today()

    def __str__(self) -> str:
        state = "open" if self.is_open else f"returned {self.returned_on}"
        return f"Loan({self.member_id} -> {self.book_isbn}, due {self.due_on}, {state})"

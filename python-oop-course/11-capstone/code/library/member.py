"""A library member."""

from library.loan import Loan


class Member:
    def __init__(self, member_id: str, name: str) -> None:
        if not member_id:
            raise ValueError("member_id must be non-empty")
        if not name:
            raise ValueError("name must be non-empty")
        self.member_id = member_id
        self.name = name
        self._loans: list[Loan] = []

    @property
    def loans(self) -> list[Loan]:
        return list(self._loans)               # defensive copy

    @property
    def active_loans(self) -> list[Loan]:
        return [ln for ln in self._loans if ln.is_open]

    def _add_loan(self, loan: Loan) -> None:
        self._loans.append(loan)

    def _replace_loan(self, old: Loan, new: Loan) -> None:
        idx = self._loans.index(old)
        self._loans[idx] = new

    def __repr__(self) -> str:
        return f"Member({self.member_id!r}, {self.name!r}, {len(self.active_loans)} active loans)"

    def __str__(self) -> str:
        return f"{self.name} (id={self.member_id})"

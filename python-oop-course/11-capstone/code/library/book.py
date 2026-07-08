"""A Book in the library's collection.

Run:
    python 11-capstone/code/cli.py list
"""


class Book:
    def __init__(self, title: str, author: str, isbn: str, copies: int = 1) -> None:
        if not title:
            raise ValueError("title must be non-empty")
        if not author:
            raise ValueError("author must be non-empty")
        if not isbn:
            raise ValueError("isbn must be non-empty")
        if copies < 1:
            raise ValueError("copies must be >= 1")
        self.title = title
        self.author = author
        self.isbn = isbn
        self._total = copies
        self._available = copies

    @property
    def total(self) -> int:
        return self._total

    @property
    def available(self) -> int:
        return self._available

    @property
    def is_available(self) -> bool:
        return self._available > 0

    def _take_one(self) -> None:
        if self._available <= 0:
            from library.errors import NoCopiesAvailable
            raise NoCopiesAvailable(f"no copies of {self.title!r} available")
        self._available -= 1

    def _return_one(self) -> None:
        if self._available >= self._total:
            raise ValueError(f"all copies of {self.title!r} already on shelf")
        self._available += 1

    def __repr__(self) -> str:
        return f"Book({self.title!r}, {self.author!r}, isbn={self.isbn!r}, available={self._available}/{self._total})"

    def __str__(self) -> str:
        return f"{self.title} — {self.author} (ISBN {self.isbn}, {self._available}/{self._total} available)"

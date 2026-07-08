"""Domain exceptions for the library system."""


class LibraryError(Exception):
    """Base for all library-specific errors."""


class BookNotFound(LibraryError):
    """Raised when a book is not in the library's collection."""


class MemberNotFound(LibraryError):
    """Raised when a member is not registered."""


class NoCopiesAvailable(LibraryError):
    """Raised when every copy of a book is already on loan."""


class LoanNotFound(LibraryError):
    """Raised when there is no open loan matching the request."""


class AlreadyReturned(LibraryError):
    """Raised when a return is attempted on an already-returned loan."""

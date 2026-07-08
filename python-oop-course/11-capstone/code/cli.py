"""A small CLI for the library system.

Run from the 11-capstone/code/ directory:
    python cli.py list
    python cli.py members
    python cli.py borrow --member m1 --isbn 978-0-13-235088-4
    python cli.py return --member m1 --isbn 978-0-13-235088-4

The CLI seeds a tiny in-memory library the first time it runs in a session.
"""

import argparse
import sys
from pathlib import Path

# Allow running as a script: add this file's directory to sys.path.
sys.path.insert(0, str(Path(__file__).parent))

from library import (  # noqa: E402
    Book,
    Library,
    LibraryError,
    Member,
)


def seed_library() -> Library:
    lib = Library("Neighborhood Library")
    lib.add_book(Book("Clean Code", "Robert C. Martin", "978-0-13-235088-4", copies=2))
    lib.add_book(Book("The Pragmatic Programmer", "Andy Hunt", "978-0-201-61622-4", copies=1))
    lib.add_book(Book("Refactoring", "Martin Fowler", "978-0-13-475759-9", copies=1))
    lib.add_member(Member("m1", "Ana"))
    lib.add_member(Member("m2", "Beto"))
    return lib


def cmd_list(lib: Library, _args: argparse.Namespace) -> int:
    for b in lib.books:
        print(b)
    return 0


def cmd_members(lib: Library, _args: argparse.Namespace) -> int:
    for m in lib.members:
        print(f"{m} — {len(m.active_loans)} active loans")
    return 0


def cmd_borrow(lib: Library, args: argparse.Namespace) -> int:
    loan = lib.borrow(args.member, args.isbn)
    print(f"borrowed: {loan}")
    return 0


def cmd_return(lib: Library, args: argparse.Namespace) -> int:
    loan = lib.return_book(args.member, args.isbn)
    print(f"returned: {loan}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Tiny library CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="list all books").set_defaults(func=cmd_list)
    sub.add_parser("members", help="list all members").set_defaults(func=cmd_members)

    b = sub.add_parser("borrow", help="borrow a book")
    b.add_argument("--member", required=True)
    b.add_argument("--isbn", required=True)
    b.set_defaults(func=cmd_borrow)

    r = sub.add_parser("return", help="return a book")
    r.add_argument("--member", required=True)
    r.add_argument("--isbn", required=True)
    r.set_defaults(func=cmd_return)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    lib = seed_library()
    try:
        return args.func(lib, args)
    except LibraryError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

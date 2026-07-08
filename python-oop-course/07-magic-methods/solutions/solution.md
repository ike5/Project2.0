# Solution 07 — Magic Methods

Reference answers. Try first.

## Key points

### Task 1 — `money.py`

```python
"""Money with arithmetic. Frozen dataclass gives us __hash__ and __eq__ for free.

Run:
    python 07-magic-methods/code/money.py
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    amount: int
    currency: str = "USD"

    def __add__(self, other: "Money") -> "Money":
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError(f"cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)


def main() -> None:
    a = Money(100, "USD")
    b = Money(50, "USD")
    print("a + b =", a + b)
    print("a + b == Money(150, 'USD') ->", (a + b) == Money(150, "USD"))
    print("hash(a) =", hash(a))


if __name__ == "__main__":
    main()
```

### Task 2 — `deck.py`

```python
"""A deck of cards that supports len, iteration, and `in`.

Run:
    python 07-magic-methods/code/deck.py
"""

import random

RANKS = "A 2 3 4 5 6 7 8 9 10 J Q K".split()
SUITS = "♠ ♥ ♦ ♣".split()


class Deck:
    def __init__(self) -> None:
        self._cards = [(r, s) for s in SUITS for r in RANKS]

    def __len__(self) -> int:
        return len(self._cards)

    def __iter__(self):
        return iter(self._cards)

    def __contains__(self, item) -> bool:
        if isinstance(item, str) and len(item) >= 2:
            rank, suit = item[:-1], item[-1]
            return (rank, suit) in self._cards
        return item in self._cards

    def shuffle(self) -> None:
        random.shuffle(self._cards)


def main() -> None:
    d = Deck()
    print("len =", len(d))
    print("A♠ in deck?", "A♠" in d)
    print("first 5 cards:", list(d)[:5])
    d.shuffle()
    print("after shuffle, first 5:", list(d)[:5])


if __name__ == "__main__":
    main()
```

### Task 3 — `open_note.py`

```python
"""A context manager that opens a file in write mode and closes it on exit.

Run:
    python 07-magic-methods/code/open_note.py
"""


class Note:
    def __init__(self, path: str) -> None:
        self.path = path
        self._f = None

    def __enter__(self):
        self._f = open(self.path, "w")
        return self._f

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._f is not None:
            self._f.close()


def main() -> None:
    with Note("/tmp/oop_note.txt") as f:
        f.write("hello from a context manager\n")
    print("wrote /tmp/oop_note.txt")


if __name__ == "__main__":
    main()
```

## Common pitfalls

- **Forgetting to return the resource from `__enter__`.** The `as` variable is whatever `__enter__` returns. If it returns `None`, `with ... as f:` binds `f` to `None`.
- **Returning `True` from `__exit__` to "swallow" exceptions.** That hides bugs. Return `False`/`None` unless you really mean to.
- **Implementing only `__eq__` and forgetting `__hash__`.** Python sets `__hash__` to `None` automatically; your object won't be hashable until you add it back.
- **Reaching for `@dataclass(frozen=True)` for a class that genuinely needs mutation.** Use a regular class or a non-frozen dataclass.

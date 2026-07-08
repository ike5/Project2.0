# Challenge 07 — Magic Methods

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **`Money` with arithmetic.** Create `07-magic-methods/code/money.py` with a frozen dataclass `Money(amount, currency)`. Add `__add__` so `Money(100, "USD") + Money(50, "USD") == Money(150, "USD")`. Add `__eq__` and `__hash__` (frozen dataclasses give you these for free — verify by removing `frozen=True` and observing what happens, then put it back). (hint: `@dataclass(frozen=True)` gives you `__hash__` and `__eq__`. You only need to add `__add__`.)
2. **`Deck` with iteration and `len`.** Create `07-magic-methods/code/deck.py` with a `Deck` class that holds a list of `(rank, suit)` tuples. Implement `__len__`, `__iter__` (yielding each card), and `__contains__` (so `"A♠" in deck` works — translate a string like `"A♠"` to a tuple and check). Include a `shuffle()` method using `random.shuffle`.
3. **`open_note` context manager.** Create `07-magic-methods/code/open_note.py` with a class `Note` that takes a path in `__init__`. `__enter__` opens the file in write mode and returns it; `__exit__` closes it. Use it as `with Note("todo.txt") as f: f.write("...")`.

## Success criteria

- [ ] `Money(100, "USD") + Money(50, "USD") == Money(150, "USD")` is `True`.
- [ ] `len(deck) == 52` (or however many cards) and `"A♠" in deck` works.
- [ ] The `Note` context manager writes and closes a file successfully.

# Challenge 06 — Composition

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **A `Computer` composed of parts.** Create `06-composition/code/computer.py` with `CPU`, `Memory`, and `Storage` classes (each with a sensible attribute and a `describe()` method returning a one-line string). Build a `Computer` that holds one of each, plus a `specs()` method that returns a multi-line description built by delegating to each part. (hint: `"\n".join(part.describe() for part in self.parts)`.)
2. **A `Money` frozen dataclass + a `Wallet` that holds money.** Create `06-composition/code/wallet.py` with:
   - `@dataclass(frozen=True) class Money: amount: int; currency: str = "USD"`
   - `class Wallet: def __init__(self, owner): self.owner = owner; self._money = {}`
   - Methods: `add(money)`, `total_in(currency) -> int` (sums the values in that currency, no conversion), and `__str__`. Use composition: a wallet *has* money, organized per currency.
3. **A `Vector2D` dataclass with arithmetic.** Create `06-composition/code/vector.py` with `@dataclass class Vector2D: x: float; y: float`. Don't override any dunder methods (yet — that's Module 07). Print a few vectors and show that `Vector2D(1, 2) == Vector2D(1, 2)` works. (hint: just `@dataclass` does it.)

## Success criteria

- [ ] `Computer` has exactly one of each part, and `specs()` returns a multi-line description.
- [ ] `Wallet` is a regular class (not a dataclass), and the `Money` it holds is a frozen dataclass.
- [ ] `Vector2D(1, 2) == Vector2D(1, 2)` is `True`; `repr(Vector2D(1, 2))` shows the fields.

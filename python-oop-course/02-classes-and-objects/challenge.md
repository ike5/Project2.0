# Challenge 02 — Classes & Objects

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Build a `BankAccount`.** Create `02-classes-and-objects/code/bank_account.py` with a `BankAccount` class that takes `owner` and an optional initial `balance=0` in `__init__`. Add `deposit(amount)`, `withdraw(amount)`, and a `balance` property (read-only — only readable from outside). Raise `ValueError` for non-positive deposits/withdrawals and for withdrawals that exceed the balance. Include a `__str__` returning `f"Account({owner}, balance={balance})"`. (hint: store the real balance in `_balance` and expose `balance` as a property; or use a simple attribute and just don't write to it from outside — both are fine for now.)
2. **Build a `Playlist`.** Create `02-classes-and-objects/code/playlist.py` with a `Playlist` class that takes a name. It should support `add(song)`, `remove(song)`, `__len__` (use `len(p)` to get song count), and `__contains__` (use `song in p`). For now, store songs in a list created in `__init__` — do not use a class attribute. (hint: `__len__` and `__contains__` are dunder methods; we cover them in detail in Module 07. For now, `def __len__(self): return len(self.songs)` and `def __contains__(self, song): return song in self.songs`.)
3. **Test both files manually.** Run each script and exercise the methods.

## Success criteria

- [ ] `BankAccount("Ana", 100).deposit(50).balance` style usage works (or use an intermediate variable). `withdraw` blocks overdraws.
- [ ] `Playlist("mix")` lets you `add`, `remove`, and ask `len(p)` and `song in p`.
- [ ] No mutable class attribute bug — each `Playlist` instance has its own song list.

# Solution 02 — Classes & Objects

Reference answers. Try the challenge first.

## Key points

### Task 1 — `bank_account.py`

```python
"""A simple BankAccount with validation and a read-only balance.

Run:
    python 02-classes-and-objects/code/bank_account.py
"""


class BankAccount:
    def __init__(self, owner: str, balance: float = 0) -> None:
        if balance < 0:
            raise ValueError("initial balance must be >= 0")
        self.owner = owner
        self._balance = balance              # "private" by convention

    @property
    def balance(self) -> float:
        return self._balance

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("deposit must be positive")
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("withdraw must be positive")
        if amount > self._balance:
            raise ValueError("insufficient funds")
        self._balance -= amount

    def __str__(self) -> str:
        return f"Account({self.owner}, balance={self._balance})"


def main() -> None:
    a = BankAccount("Ana", 100)
    print(a)
    a.deposit(50)
    a.withdraw(30)
    print(a)

    try:
        a.withdraw(10_000)
    except ValueError as e:
        print("blocked:", e)

    try:
        a.deposit(-5)
    except ValueError as e:
        print("blocked:", e)


if __name__ == "__main__":
    main()
```

> We use `@property` here so `balance` is read-only from outside. The next module goes deep on properties.

### Task 2 — `playlist.py`

```python
"""A Playlist with add, remove, len, and `in` support.

Run:
    python 02-classes-and-objects/code/playlist.py
"""


class Playlist:
    def __init__(self, name: str) -> None:
        self.name = name
        self.songs = []                       # instance attribute, not class

    def add(self, song: str) -> None:
        self.songs.append(song)

    def remove(self, song: str) -> None:
        if song not in self.songs:
            raise ValueError(f"{song!r} not in playlist")
        self.songs.remove(song)

    def __len__(self) -> int:
        return len(self.songs)

    def __contains__(self, song: str) -> bool:
        return song in self.songs

    def __str__(self) -> str:
        return f"Playlist({self.name!r}, {len(self)} songs)"


def main() -> None:
    p = Playlist("morning mix")
    p.add("Clair de Lune")
    p.add("Gymnopédie No. 1")
    print(p)
    print("contains Clair de Lune?", "Clair de Lune" in p)
    p.remove("Clair de Lune")
    print(p)
    print("contains Clair de Lune?", "Clair de Lune" in p)


if __name__ == "__main__":
    main()
```

## Common pitfalls

- **Putting `songs = []` at class level.** Every `Playlist` would share the same list. The lab is the whole reason we covered this in the README.
- **Trying to make `balance` truly read-only without using `@property`.** You can use `__balance` (name-mangled, Module 03), but `@property` is the standard, clean answer.
- **Forgetting to return from `__len__`.** It *must* return an `int`. Returning `None` will give you a confusing error in `len(p)`.

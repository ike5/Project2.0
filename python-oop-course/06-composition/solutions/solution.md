# Solution 06 — Composition

Reference answers. Try first.

## Key points

### Task 1 — `computer.py`

```python
"""A Computer composed of CPU, Memory, and Storage.

Run:
    python 06-composition/code/computer.py
"""


class CPU:
    def __init__(self, model: str, cores: int) -> None:
        self.model = model
        self.cores = cores

    def describe(self) -> str:
        return f"CPU: {self.model} ({self.cores} cores)"


class Memory:
    def __init__(self, size_gb: int) -> None:
        self.size_gb = size_gb

    def describe(self) -> str:
        return f"Memory: {self.size_gb} GB"


class Storage:
    def __init__(self, size_gb: int, kind: str) -> None:
        self.size_gb = size_gb
        self.kind = kind

    def describe(self) -> str:
        return f"Storage: {self.size_gb} GB {self.kind}"


class Computer:
    def __init__(self, cpu: CPU, memory: Memory, storage: Storage) -> None:
        self.cpu = cpu
        self.memory = memory
        self.storage = storage

    def specs(self) -> str:
        return "\n".join([
            self.cpu.describe(),
            self.memory.describe(),
            self.storage.describe(),
        ])


def main() -> None:
    c = Computer(CPU("M2", 8), Memory(16), Storage(512, "SSD"))
    print(c.specs())


if __name__ == "__main__":
    main()
```

### Task 2 — `wallet.py`

```python
"""A Wallet that holds Money (a frozen dataclass).

Run:
    python 06-composition/code/wallet.py
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Money:
    amount: int
    currency: str = "USD"


class Wallet:
    def __init__(self, owner: str) -> None:
        self.owner = owner
        self._money: dict[str, int] = {}     # currency -> total cents

    def add(self, money: Money) -> None:
        self._money[money.currency] = self._money.get(money.currency, 0) + money.amount

    def total_in(self, currency: str) -> int:
        return self._money.get(currency, 0)

    def __str__(self) -> str:
        parts = [f"{amt} {cur}" for cur, amt in self._money.items()]
        return f"Wallet({self.owner}: {', '.join(parts) or 'empty'})"


def main() -> None:
    w = Wallet("Ana")
    w.add(Money(100))
    w.add(Money(250))
    w.add(Money(50, "EUR"))
    print(w)
    print("USD total:", w.total_in("USD"))
    print("EUR total:", w.total_in("EUR"))


if __name__ == "__main__":
    main()
```

### Task 3 — `vector.py`

```python
"""A Vector2D dataclass. Equality and repr come for free.

Run:
    python 06-composition/code/vector.py
"""

from dataclasses import dataclass


@dataclass
class Vector2D:
    x: float
    y: float


def main() -> None:
    a = Vector2D(1, 2)
    b = Vector2D(1, 2)
    print("a      =", a)
    print("repr(a)=", repr(a))
    print("a == b ->", a == b)


if __name__ == "__main__":
    main()
```

## Common pitfalls

- **Reaching for `@dataclass` when the class needs heavy validation in `__init__`.** Dataclasses are great for data, but if your class has invariants that have to be checked, write `__init__` explicitly or use `__post_init__`.
- **Storing the same list in every instance via a class-attribute default.** That's the bug from Module 02. `default_factory=list` is the cure.
- **Confusing "frozen" with "secret."** `frozen=True` blocks *assignment* in Python. It doesn't make the value truly immutable at the C level.

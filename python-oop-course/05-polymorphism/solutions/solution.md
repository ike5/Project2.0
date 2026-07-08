# Solution 05 — Polymorphism

Reference answers. Try first.

## Key points

### Task 1 — `notifier.py` (duck typing)

```python
"""Three notifiers, one entry point.

Run:
    python 05-polymorphism/code/notifier.py
"""


class EmailNotifier:
    def send(self, to: str, message: str) -> None:
        print(f"email -> {to}: {message}")


class SMSNotifier:
    def send(self, to: str, message: str) -> None:
        print(f"sms   -> {to}: {message}")


class LogNotifier:
    def send(self, to: str, message: str) -> None:
        print(f"log: would deliver '{message}' to {to}")


def notify_all(notifiers, to: str, message: str) -> None:
    for n in notifiers:
        n.send(to, message)


def main() -> None:
    notify_all(
        [EmailNotifier(), SMSNotifier(), LogNotifier()],
        "ana",
        "build is green",
    )


if __name__ == "__main__":
    main()
```

### Task 2 — `exporter.py` (ABC)

```python
"""An Exporter ABC with two concrete exporters.

Run:
    python 05-polymorphism/code/exporter.py
"""

import json
from abc import ABC, abstractmethod


class Exporter(ABC):
    @abstractmethod
    def export(self, data: str) -> str: ...


class JSONExporter(Exporter):
    def export(self, data: str) -> str:
        return json.dumps({"data": data})


class CSVExporter(Exporter):
    def export(self, data: str) -> str:
        return "data\n" + data


def export_all(exporters, data: str) -> None:
    for e in exporters:
        print(type(e).__name__, "->", e.export(data))


def main() -> None:
    export_all([JSONExporter(), CSVExporter()], "hello")
    try:
        Exporter()
    except TypeError as e:
        print("\nExporter() raised:", e)


if __name__ == "__main__":
    main()
```

### Task 3 — `speaker_proto.py` (Protocol)

```python
"""A Speaker Protocol satisfied by three unrelated classes.

Run:
    python 05-polymorphism/code/speaker_proto.py
"""

from typing import Protocol


class Speaker(Protocol):
    def speak(self) -> str: ...


class Dog:
    def speak(self) -> str:
        return "Rex: woof!"


class Human:
    def speak(self) -> str:
        return "hi, I'm Ana"


class PhoneAssistant:
    def speak(self) -> str:
        return "Hello, how can I help?"


def announce(speaker) -> None:
    print(speaker.speak())


def main() -> None:
    for s in (Dog(), Human(), PhoneAssistant()):
        announce(s)


if __name__ == "__main__":
    main()
```

## Common pitfalls

- **Inheriting from `Protocol` instead of declaring it.** A `Protocol` is a *type hint*, not a base class. The classes that satisfy it don't need to import it.
- **Putting a `pass` body in an ABC method with no docstring.** Python will complain less if you write `...` (an `Ellipsis`). The body is irrelevant because the method is abstract.
- **Confusing "Protocol" with ABC.** `Protocol` is for type-checkers; `ABC` is for runtime enforcement. Pick the one that matches the kind of guarantee you want.

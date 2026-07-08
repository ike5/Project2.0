# Challenge 05 — Polymorphism

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Polymorphic `Notifier`.** Create `05-polymorphism/code/notifier.py` with three classes — `EmailNotifier`, `SMSNotifier`, `LogNotifier` — each with a `send(self, to: str, message: str) -> None` method that prints a line appropriate to its medium. Then write `def notify_all(notifiers, to, message)` that loops over the list and calls `send` on each. (hint: no base class needed; this is duck typing.)
2. **An `Exporter` ABC.** Create `05-polymorphism/code/exporter.py` with an `Exporter` ABC that requires `export(self, data: str) -> str`. Implement `JSONExporter` and `CSVExporter`. Show that calling `Exporter()` raises `TypeError`. Then write `def export_all(exporters, data)` that loops and prints the result. (hint: ABCs come from `abc`.)
3. **A `Speaker` Protocol.** Create `05-polymorphism/code/speaker_proto.py` with a `Speaker` Protocol requiring `speak(self) -> str`. Make `Dog`, `Human`, and `PhoneAssistant` classes (no shared base, no ABC) and write `def announce(speaker)` that calls `speak()`. (hint: `from typing import Protocol`.)

## Success criteria

- [ ] Task 1: `notify_all([EmailNotifier(), SMSNotifier(), LogNotifier()], "ana", "hi")` prints three lines.
- [ ] Task 2: `Exporter()` raises `TypeError`; `export_all([JSONExporter(), CSVExporter()], "x")` prints two outputs.
- [ ] Task 3: `announce(...)` works for all three `Speaker` types, none of which inherit from `Speaker`.

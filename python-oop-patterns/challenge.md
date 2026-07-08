# Challenge 09 — Design Patterns

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Strategy: a `TaxCalculator`.** Create `09-design-patterns/code/tax.py` with a `TaxCalculator` that takes a `strategy` (a function `(amount) -> tax`) in `__init__`. Provide two strategies as functions: `flat_rate(amount)` (15%) and `progressive(amount)` (10% up to 1000, 20% above). Demonstrate both with `TaxCalculator(flat_rate).compute(1500)`.
2. **Observer: a `Newsfeed`.** Create `09-design-patterns/code/newsfeed.py` with a `Newsfeed` subject that stores a list of headlines. Methods: `add_headline(text)`, `subscribe(fn)`, `unsubscribe(fn)`. On every add, all subscribers are called with the new headline. Add two subscribers: one that prints, one that counts the headlines and prints the count.
3. **Decorator pattern: a `Logger` wrapper.** Create `09-design-patterns/code/logged.py` with a `Logger` class with a `log(msg)` method that prints `msg`. Then create `TimestampedLogger` and `UpperLogger` that wrap a `Logger` and add behavior (prefix the message with a timestamp; uppercase the message). Show that wrapping `TimestampedLogger(UpperLogger(Logger()))` works as expected.
4. **Factory: a `Notifier.for(channel)`.** Create `09-design-patterns/code/notifier_factory.py` with a `Notifier` base and `EmailNotifier`/`SMSNotifier`/`PushNotifier` subclasses (each with a `send(to, msg)` method). Add a `Notifier.for(channel: str)` classmethod that returns the right subclass based on the channel name.
5. **Adapter: a `LoggerAdapter` for `print`.** Create `09-design-patterns/code/logger_adapter.py` that adapts the built-in `print` to a class with a `log(msg)` method, using an Adapter.

## Success criteria

- [ ] `TaxCalculator(progressive).compute(1500) == 250.0` (10% on 1000 + 20% on 500).
- [ ] `Newsfeed` calls all subscribers on each add and the counter ends at the right value.
- [ ] `TimestampedLogger(UpperLogger(Logger())).log("hi")` produces an uppercased, timestamped line.
- [ ] `Notifier.for("email")` returns an `EmailNotifier`.
- [ ] `LoggerAdapter` calls `print` when `.log(...)` is invoked.

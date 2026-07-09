"""Notifier factory — build the right subclass by name.

Run me: python 07-factory-pattern/code/notifier_factory.py
"""


class Notifier:
    def send(self, to: str, msg: str) -> None:
        raise NotImplementedError

    @classmethod
    def for_channel(cls, channel: str) -> "Notifier":
        return _registry[channel]()


class EmailNotifier(Notifier):
    def send(self, to: str, msg: str) -> None:
        print(f"[email to {to}] {msg}")


class SMSNotifier(Notifier):
    def send(self, to: str, msg: str) -> None:
        print(f"[SMS to {to}] {msg}")


class PushNotifier(Notifier):
    def send(self, to: str, msg: str) -> None:
        print(f"[push to {to}] {msg}")


_registry: dict[str, type[Notifier]] = {
    "email": EmailNotifier,
    "sms":   SMSNotifier,
    "push":  PushNotifier,
}


def main() -> None:
    for channel, target in [("email", "alice@example.com"),
                             ("sms",   "+1-555-0100"),
                             ("push",  "device-abc")]:
        n = Notifier.for_channel(channel)
        n.send(target, "Hello!")


if __name__ == "__main__":
    main()

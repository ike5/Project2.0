"""Observer: a Subject that broadcasts value changes to a list of subscribers.

Run:
    python 09-design-patterns/code/observer.py
"""


class Subject:
    def __init__(self) -> None:
        self._observers = []
        self._value = None

    def subscribe(self, fn) -> None:
        self._observers.append(fn)

    def unsubscribe(self, fn) -> None:
        self._observers.remove(fn)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v) -> None:
        self._value = v
        for fn in list(self._observers):
            fn(v)


def main() -> None:
    s = Subject()
    s.subscribe(lambda v: print(f"  logger1: value -> {v}"))
    s.subscribe(lambda v: print(f"  logger2: {type(v).__name__} = {v}"))
    s.value = 1
    s.value = "hi"
    s.value = [1, 2, 3]


if __name__ == "__main__":
    main()

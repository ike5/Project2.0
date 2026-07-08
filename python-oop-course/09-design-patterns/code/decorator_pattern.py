"""GoF Decorator pattern: stack wrappers that share the same interface.

Run:
    python 09-design-patterns/code/decorator_pattern.py
"""


class Text:
    def __init__(self, s: str) -> None:
        self.s = s

    def render(self) -> str:
        return self.s


class Bold:
    def __init__(self, inner) -> None:
        self.inner = inner

    def render(self) -> str:
        return f"<b>{self.inner.render()}</b>"


class Italic:
    def __init__(self, inner) -> None:
        self.inner = inner

    def render(self) -> str:
        return f"<i>{self.inner.render()}</i>"


def main() -> None:
    plain = Text("hi")
    print(plain.render())
    print(Bold(plain).render())
    print(Italic(plain).render())
    print(Bold(Italic(plain)).render())


if __name__ == "__main__":
    main()

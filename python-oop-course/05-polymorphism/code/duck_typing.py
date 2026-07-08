"""Duck typing: a function that calls a method, regardless of type.

Run:
    python 05-polymorphism/code/duck_typing.py
"""


class Duck:
    def quack(self) -> str:
        return "quack!"


class Person:
    def quack(self) -> str:
        return "I am pretending to be a duck"


class Speaker:
    def quack(self) -> str:
        return "(speaker noise that vaguely sounds like quack)"


def make_it_quack(thing) -> str:
    return thing.quack()


def main() -> None:
    for thing in (Duck(), Person(), Speaker()):
        print(f"{type(thing).__name__:>8}  ->  {make_it_quack(thing)}")


if __name__ == "__main__":
    main()

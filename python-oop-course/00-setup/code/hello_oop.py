"""Hello, OOP: the smallest possible class.

Defines a class, creates an instance, calls a method. Prints what happens so
you can confirm your environment works before Module 01.

Run:
    python 00-setup/code/hello_oop.py
"""


class Dog:
    """A very simple class with one piece of state and one method."""

    def __init__(self, name: str) -> None:
        self.name = name

    def bark(self) -> str:
        return f"{self.name} says woof!"


def main() -> None:
    print("hello, oop")
    rex = Dog("Rex")
    print(rex.bark())


if __name__ == "__main__":
    main()

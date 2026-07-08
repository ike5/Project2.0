"""Explore the claim "everything in Python is an object."

We pass a handful of familiar values to type() and dir() to see what Python
already knows about them — and to show that the things we will learn to build
(class instances) are not fundamentally different from the things Python ships
with (ints, lists, functions).

Run:
    python 01-oop-foundations/code/explore_objects.py
"""


def section(title: str) -> None:
    print(f"\n--- {title} ---")


def show_type(label: str, value) -> None:
    print(f"type({label:>14})  ->  {type(value).__name__}")


def show_attr_count(label: str, value) -> None:
    print(f"dir({label:>14})  has  {len(dir(value))} attributes")


def main() -> None:
    section("1. Types of everyday values")
    show_type("42", 42)
    show_type("3.14", 3.14)
    show_type("'hi'", "hi")
    show_type("[1, 2]", [1, 2])
    show_type("(1, 2, 3)", (1, 2, 3))
    show_type("{'a': 1}", {"a": 1})
    show_type("True", True)
    show_type("None", None)
    show_type("print", print)

    section("2. Objects have attributes")
    show_attr_count("42", 42)
    show_attr_count("'hello'", "hello")
    show_attr_count("[1, 2]", [1, 2])
    show_attr_count("(1, 2, 3)", (1, 2, 3))

    section("3. A peek at the attributes of a tuple")
    print("first 10 of dir((1, 2, 3)):")
    for name in dir((1, 2, 3))[:10]:
        print(f"  - {name}")

    section("4. Methods are attributes that happen to be callable")
    sample = "hello"
    upper = sample.upper            # grab the bound method
    print(f"'hello'.upper  ->  {upper}")
    print(f"calling it     ->  {upper()}")


if __name__ == "__main__":
    main()

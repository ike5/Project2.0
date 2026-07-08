"""Procedural vs. object-oriented, side by side.

A small program written two ways. Both produce the same output. The point is
to feel how similar they are, and to see the pieces that become "the class."

Run:
    python 01-oop-foundations/code/dog_procedural_vs_oop.py

After running, you can keep using the Dog class in a REPL:
    python -i 01-oop-foundations/code/dog_procedural_vs_oop.py
"""

# --- Procedural -------------------------------------------------------------

def make_dog(name: str, age: int) -> dict:
    return {"name": name, "age": age}


def dog_bark(d: dict) -> str:
    return f"{d['name']}: woof!"


# --- Object-oriented --------------------------------------------------------

class Dog:
    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age

    def bark(self) -> str:
        return f"{self.name}: woof!"


def main() -> None:
    print("procedural:", dog_bark(make_dog("Rex", 4)))
    print("oop:       ", Dog("Rex", 4).bark())


if __name__ == "__main__":
    main()

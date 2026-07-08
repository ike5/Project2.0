"""Protocol-based polymorphism: three classes that all draw() but don't share a base.

Run:
    python 05-polymorphism/code/protocol_render.py
"""

from typing import Protocol


class Drawable(Protocol):
    def draw(self) -> None: ...


class Circle:
    def draw(self) -> None: print("○")


class Square:
    def draw(self) -> None: print("□")


class Text:
    def draw(self) -> None: print("text rendered")


def render(obj: Drawable) -> None:
    obj.draw()


def main() -> None:
    for obj in (Circle(), Square(), Text()):
        render(obj)
    print()
    print("type of each:", [type(o).__name__ for o in (Circle(), Square(), Text())])
    print("(no common base, but they all satisfy the Drawable protocol.)")


if __name__ == "__main__":
    main()

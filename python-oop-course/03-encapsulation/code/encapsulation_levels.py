"""Public, _protected, and __mangled attributes, demonstrated.

Run:
    python 03-encapsulation/code/encapsulation_levels.py
"""


class Account:
    def __init__(self) -> None:
        self.public = "I am public"           # anyone can read or write
        self._protected = "convention: don't touch me"
        self.__private = "name-mangled: harder to reach"


def main() -> None:
    a = Account()
    print("a.public       ->", a.public)
    print("a._protected   ->", a._protected)            # works, but please don't
    try:
        print("a.__private    ->", a.__private)
    except AttributeError as e:
        print("a.__private    -> AttributeError:", e)

    mangled = "_Account__private"
    print(f"a.{mangled} ->", getattr(a, mangled))


if __name__ == "__main__":
    main()

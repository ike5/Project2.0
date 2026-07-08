"""super() in __init__ and in overridden methods.

Run:
    python 04-inheritance/code/super_demo.py
"""


class Animal:
    def __init__(self, name: str) -> None:
        print(f"  Animal.__init__({name!r})")
        self.name = name

    def speak(self) -> str:
        return f"{self.name}: ..."


class Dog(Animal):
    def __init__(self, name: str, breed: str) -> None:
        print(f"  Dog.__init__({name!r}, {breed!r})")
        super().__init__(name)
        self.breed = breed

    def speak(self) -> str:
        parent = super().speak()               # "Rex: ..."
        return f"{parent}  [then] woof!"


def main() -> None:
    print("Building a Dog:")
    d = Dog("Rex", "lab")
    print()
    print("d.breed =", d.breed)
    print("d.name  =", d.name)
    print("d.speak():", d.speak())


if __name__ == "__main__":
    main()

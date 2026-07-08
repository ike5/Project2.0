"""Single-inheritance chain: Animal -> Dog -> Puppy.

Run:
    python 04-inheritance/code/basic_inheritance.py
"""


class Animal:
    def __init__(self, name: str) -> None:
        self.name = name

    def speak(self) -> str:
        return "..."

    def __str__(self) -> str:
        return f"{type(self).__name__}({self.name})"


class Dog(Animal):
    def speak(self) -> str:
        return f"{self.name}: woof!"


class Puppy(Dog):
    def speak(self) -> str:
        return super().speak().replace("woof", "yip")


def main() -> None:
    a = Animal("Creature")
    d = Dog("Rex")
    p = Puppy("Pip")

    for animal in (a, d, p):
        print(f"{animal}.speak() -> {animal.speak()}")

    print()
    print("MROs:")
    for cls in (Animal, Dog, Puppy):
        print(f"  {cls.__name__}.mro() = {[c.__name__ for c in cls.mro()]}")


if __name__ == "__main__":
    main()

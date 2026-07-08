"""A Dog class with several method flavors: returning, mutating, taking args.

Run:
    python 02-classes-and-objects/code/dog_methods.py
"""


class Dog:
    species = "Canis familiaris"

    def __init__(self, name: str, age: int) -> None:
        if not name:
            raise ValueError("name must be non-empty")
        if age < 0:
            raise ValueError("age must be >= 0")
        self.name = name
        self.age = age

    def bark(self) -> str:
        return f"{self.name}: woof!"

    def have_birthday(self) -> None:
        self.age += 1

    def is_puppy(self) -> bool:
        return self.age < 2

    def greet(self, other: "Dog") -> str:
        return f"{self.name} sniffs {other.name}"


def main() -> None:
    rex = Dog("Rex", 2)
    buddy = Dog("Buddy", 5)
    print(rex.bark())
    print(rex.greet(buddy))
    print("Rex is a puppy:", rex.is_puppy())
    rex.have_birthday()
    print("after birthday, Rex is", rex.age)
    print("species of every dog:", Dog.species)


if __name__ == "__main__":
    main()

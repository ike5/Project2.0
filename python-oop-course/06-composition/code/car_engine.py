"""Composition: a Car that holds an Engine and delegates to it.

Run:
    python 06-composition/code/car_engine.py
"""


class Engine:
    def __init__(self, horsepower: int) -> None:
        self.horsepower = horsepower

    def start(self) -> str:
        return f"engine ({self.horsepower} hp) running"


class Car:
    def __init__(self, make: str, engine: Engine) -> None:
        self.make = make
        self.engine = engine

    def start(self) -> str:
        return f"{self.make}: {self.engine.start()}"

    def set_engine(self, engine: Engine) -> None:
        self.engine = engine                 # swap parts at runtime


def main() -> None:
    car = Car("Toyota", Engine(150))
    print(car.start())
    car.set_engine(Engine(300))
    print(car.start())


if __name__ == "__main__":
    main()

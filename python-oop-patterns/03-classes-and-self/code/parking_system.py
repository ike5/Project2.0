"""The ParkingSystem class from LeetCode 1603.

Run me: python 03-classes-and-self/code/parking_system.py
"""


class ParkingSystem:
    def __init__(self, big: int, medium: int, small: int) -> None:
        # 1=big, 2=medium, 3=small; index by carType - 1
        self.slots = [big, medium, small]

    def addCar(self, carType: int) -> bool:
        if self.slots[carType - 1] == 0:
            return False
        self.slots[carType - 1] -= 1
        return True


def main() -> None:
    ps = ParkingSystem(1, 1, 0)
    print(ps.addCar(1))   # True   (big slot used)
    print(ps.addCar(2))   # True   (medium slot used)
    print(ps.addCar(3))   # False  (no small slots)
    print(ps.addCar(1))   # False  (no more big slots)


if __name__ == "__main__":
    main()

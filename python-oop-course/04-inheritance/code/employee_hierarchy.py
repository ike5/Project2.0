"""A small Employee -> Manager / Engineer hierarchy.

Run:
    python 04-inheritance/code/employee_hierarchy.py
"""


class Employee:
    def __init__(self, name: str, years: int) -> None:
        self.name = name
        self.years = years

    def describe(self) -> str:
        return f"{self.name} ({self.years} yr)"

    def role(self) -> str:
        return "Employee"


class Engineer(Employee):
    def __init__(self, name: str, years: int, stack: str) -> None:
        super().__init__(name, years)
        self.stack = stack

    def role(self) -> str:
        return "Engineer"

    def describe(self) -> str:
        return f"{super().describe()} — {self.role()} on {self.stack}"


class Manager(Employee):
    def __init__(self, name: str, years: int, team_size: int) -> None:
        super().__init__(name, years)
        self.team_size = team_size

    def role(self) -> str:
        return "Manager"

    def describe(self) -> str:
        return f"{super().describe()} — {self.role()} of {self.team_size}"


def main() -> None:
    e = Engineer("Mia", 4, "Python")
    m = Manager("Jules", 9, 6)
    print(e.describe())
    print(m.describe())
    print("MRO Manager:", [c.__name__ for c in Manager.mro()])
    print("isinstance m Employee:", isinstance(m, Employee))


if __name__ == "__main__":
    main()

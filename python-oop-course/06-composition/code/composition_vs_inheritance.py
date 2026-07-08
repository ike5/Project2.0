"""Inheritance vs. composition, on the same domain.

Both versions model a 'User' that has profile info. The inheritance version
puts profile data on a base class; the composition version gives User a
Profile object and delegates to it.

Run:
    python 06-composition/code/composition_vs_inheritance.py
"""


# --- Inheritance: User IS-A Profile (forced is-a) ---------------------------

class Profile:
    def __init__(self, name: str, email: str) -> None:
        self.name = name
        self.email = email

    def contact_card(self) -> str:
        return f"{self.name} <{self.email}>"


class User(Profile):                          # User "is a" Profile (a stretch)
    def __init__(self, name: str, email: str, role: str) -> None:
        super().__init__(name, email)
        self.role = role


# --- Composition: User HAS-A Profile ----------------------------------------


class Profile2:
    def __init__(self, name: str, email: str) -> None:
        self.name = name
        self.email = email

    def contact_card(self) -> str:
        return f"{self.name} <{self.email}>"


class User2:
    def __init__(self, profile: Profile2, role: str) -> None:
        self.profile = profile                # has-a
        self.role = role

    def contact_card(self) -> str:
        return self.profile.contact_card()    # delegate


def main() -> None:
    u1 = User("Ana", "ana@example.com", "admin")
    u2 = User2(Profile2("Ana", "ana@example.com"), "admin")
    print("inheritance :", u1.contact_card(), "— role =", u1.role)
    print("composition :", u2.contact_card(), "— role =", u2.role)
    # In the composition version, you can swap the Profile out:
    u2.profile = Profile2("Ana B.", "anab@example.com")
    print("after swap  :", u2.contact_card())


if __name__ == "__main__":
    main()

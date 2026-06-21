"""Structured output: get validated Pydantic objects out of the model, not prose.

Run:
    python 03-structured-output-and-tools/code/structured_output.py

Needs a running local Ollama server (ollama serve). Prints the typed objects and accesses their fields so you
can see you're holding real Python attributes, not text you have to parse.
"""

from typing import Optional

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field


# --- A simple schema: two scalars plus an optional field ---------------------
class Person(BaseModel):
    name: str = Field(description="the person's full name")
    age: int = Field(description="age in years")
    email: Optional[str] = Field(default=None, description="email if mentioned, else null")


# --- A nested schema: a model that contains a list of other models -----------
class Skill(BaseModel):
    name: str = Field(description="name of the skill")
    years: int = Field(description="years of experience with it")


class Profile(BaseModel):
    name: str = Field(description="the person's full name")
    title: str = Field(description="their job title")
    skills: list[Skill] = Field(default_factory=list, description="skills they have")


def section(title: str) -> None:
    print("\n" + "-" * 60)
    print(title)
    print("-" * 60)


def main() -> None:
    model = ChatOllama(model="llama3.1", num_predict=1024)

    section("1. Simple schema (with an Optional field)")
    structured = model.with_structured_output(Person)

    p1 = structured.invoke("Grace Hopper was a 79-year-old computer scientist.")
    print("type:", type(p1).__name__)
    print("p1:  ", p1)
    print("name:", p1.name, "| age:", p1.age, "| age+1 =", p1.age + 1)
    print("email (not in text, so None):", p1.email)

    p2 = structured.invoke("Ada Lovelace, 36, can be reached at ada@analytical.engine.")
    print("\np2 email (mentioned):", p2.email)

    section("2. Nested schema: a Profile with a list of Skill objects")
    profile_model = model.with_structured_output(Profile)
    prof = profile_model.invoke(
        "Lin is a staff engineer. She's done 8 years of Python and 3 years of Rust."
    )
    print("name :", prof.name)
    print("title:", prof.title)
    for s in prof.skills:
        print(f"  - {s.name}: {s.years} yr   (type {type(s).__name__})")
    print("first skill, typed access:", prof.skills[0].name, "->", prof.skills[0].years)

    print("\nDone. Notice: no json.loads, no regex — just attributes off a Python object.")


if __name__ == "__main__":
    main()

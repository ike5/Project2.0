"""Write the capstone's sample knowledge base to disk (idempotent).

The reference solution and the starter both retrieve over a small, fictional
product manual. This module owns that text so every script can share it and run
standalone — no network, no second API key.

Run (writes/refreshes kb.txt next to this file, then prints a preview):
    python 07-capstone/code/sample_kb.py

Import elsewhere with:
    from sample_kb import ensure_kb
    kb_path = ensure_kb()      # returns the absolute path to kb.txt
"""

from pathlib import Path

# Where kb.txt lives: right next to this script, so retrieval works no matter
# which directory you run from.
KB_PATH = Path(__file__).with_name("kb.txt")

# A small, fact-dense manual for a *fictional* product. The facts are specific
# and unguessable on purpose, so you can tell when the agent actually retrieved
# them versus when it made something up.
KB_TEXT = """\
# Lumen Mug — Product Manual

## Overview
The Lumen Mug is a self-heating travel mug made by Northwind Devices. It keeps
your drink at a temperature you choose, anywhere from 50°C to 65°C, for up to
six hours on a single charge. The mug holds 414 millilitres (14 fluid ounces).
It ships in three colours: Slate, Sand, and Forest.

## Battery and charging
The Lumen Mug contains a removable 3200 mAh lithium-ion battery. It charges on
the included magnetic charging coaster over roughly 90 minutes from empty to
full. A full charge holds the set temperature for about six hours, or keeps the
drink merely warm for up to ten hours. The LED ring on the base glows amber
while charging and turns solid white when the battery is full.

## Setting the temperature
Press and hold the single button on the base for two seconds to wake the mug.
Each short press then cycles the target temperature up by 5°C, wrapping back to
50°C after 65°C. The LED ring colour indicates the setting: blue is 50°C, green
is 55°C, orange is 60°C, and red is 65°C. The mug remembers your last setting
between uses.

## Care and cleaning
The Lumen Mug is NOT dishwasher safe. Hand-wash the cup with warm soapy water
and avoid submerging the base, which holds the electronics. Do not put the mug
in a microwave. The lid and the silicone seal are both dishwasher safe on the
top rack only.

## Warranty and support
Northwind Devices offers a two-year limited warranty on the Lumen Mug, covering
manufacturing defects but not water damage from submerging the base. Register
your mug within 30 days of purchase to extend the warranty to three years.
Support is reachable at support@northwind.example and replies within two
business days.
"""


def ensure_kb() -> str:
    """Write kb.txt if it is missing or out of date, and return its path.

    Idempotent: safe to call from every script on every run. Returns the
    absolute path as a string so callers can hand it straight to TextLoader.
    """
    if not KB_PATH.exists() or KB_PATH.read_text(encoding="utf-8") != KB_TEXT:
        KB_PATH.write_text(KB_TEXT, encoding="utf-8")
    return str(KB_PATH)


if __name__ == "__main__":
    path = ensure_kb()
    print(f"Wrote knowledge base to: {path}")
    print(f"Length: {len(KB_TEXT)} characters, {KB_TEXT.count(chr(10)) + 1} lines\n")
    print("--- preview (first 8 lines) ---")
    for line in KB_TEXT.splitlines()[:8]:
        print(line)

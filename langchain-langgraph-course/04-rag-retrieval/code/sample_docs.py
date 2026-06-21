"""Write a small sample knowledge file so the RAG scripts have something to find.

Run:
    python 04-rag-retrieval/code/sample_docs.py

Creates `04-rag-retrieval/code/notes.txt` (if missing) with ~8 short factual
paragraphs about a fictional product. Other scripts import `ensure_docs()` to get
the path, creating the file on demand so everything runs standalone.
"""

from pathlib import Path

# The sample knowledge base. Everything here is MADE UP — that's the point: the
# model can't know these facts from pre-training, so a correct answer can only
# come from retrieval. Each paragraph is one self-contained fact.
NOTES = """\
Lumina is a rechargeable smart desk lamp made by the fictional company Northwind Labs.
It was first released in March 2023 and is sold only through the company's website.

The Lumina lamp has a battery that lasts about 18 hours on a single charge at medium
brightness. Charging from empty to full takes roughly 2.5 hours over USB-C.

Lumina supports five brightness levels and three color temperatures: warm (2700K),
neutral (4000K), and cool (5000K). You cycle temperatures by double-tapping the base.

The lamp connects to the Northwind app over Bluetooth. Through the app you can set
schedules, create lighting scenes, and check the remaining battery percentage.

Northwind Labs offers a two-year limited warranty on the Lumina. The warranty covers
manufacturing defects but does not cover water damage or a cracked lampshade.

If the Lumina will not turn on, hold the power button for ten seconds to force a reset.
If that fails, charge it for at least thirty minutes before trying again.

The Lumina weighs 1.1 kilograms and stands 42 centimeters tall. The base is machined
aluminum and the shade is recycled polycarbonate. It ships in plastic-free packaging.

Northwind Labs was founded in 2019 in Portland, Oregon. The Lumina is its first
consumer product; the company previously made lighting controllers for offices.
"""


def ensure_docs() -> Path:
    """Return the path to notes.txt, creating it with sample content if missing."""
    path = Path(__file__).with_name("notes.txt")
    if not path.exists():
        path.write_text(NOTES, encoding="utf-8")
    return path


def main() -> None:
    path = ensure_docs()
    text = path.read_text(encoding="utf-8")
    paras = [p for p in text.split("\n\n") if p.strip()]
    print(f"Wrote / found knowledge file: {path}")
    print(f"  {len(paras)} paragraphs, {len(text)} characters")
    print("\nFirst paragraph:\n  " + paras[0].replace("\n", " "))


if __name__ == "__main__":
    main()

"""Demos of Counter and defaultdict.

Run me: python 01-dicts-as-maps/code/counter_defaultdict.py
"""

from collections import Counter, defaultdict


def demo_counter() -> None:
    c = Counter("abracadabra")
    print("top 2 chars:", c.most_common(2))


def demo_defaultdict() -> None:
    words = ["the", "and", "to", "a", "i", "be", "of"]
    groups: defaultdict[int, list[str]] = defaultdict(list)
    for w in words:
        groups[len(w)].append(w)
    print("groups by length:", dict(groups))


def main() -> None:
    demo_counter()
    demo_defaultdict()


if __name__ == "__main__":
    main()

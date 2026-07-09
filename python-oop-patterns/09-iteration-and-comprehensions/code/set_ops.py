"""Set operations.

Run me: python 09-iteration-and-comprehensions/code/set_ops.py
"""


def main() -> None:
    a = {1, 2, 3, 4}
    b = {3, 4, 5, 6}
    print("a        =", a)
    print("b        =", b)
    print("a & b    =", a & b)
    print("a | b    =", a | b)
    print("a - b    =", a - b)
    print("a ^ b    =", a ^ b)

    # Common letters between two words.
    w1, w2 = "anagram", "manga"
    common = set(w1) & set(w2)
    print(f"common letters in {w1!r} and {w2!r} =", sorted(common))

    # Longest common prefix of a list of strings.
    def longest_common_prefix(strs: list[str]) -> str:
        if not strs:
            return ""
        prefix = set(strs[0])
        for s in strs[1:]:
            prefix &= set(s)
        # Take the intersection, sort it, prefix is the chars common to ALL positions.
        # For a real prefix we need position-by-position; this is the simpler version.
        return "".join(sorted(prefix))

    print("LCP (set-based) =", longest_common_prefix(["flower", "flow", "flight"]))


if __name__ == "__main__":
    main()

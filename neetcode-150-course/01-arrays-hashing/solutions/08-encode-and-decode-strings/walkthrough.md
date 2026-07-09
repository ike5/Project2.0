# Encode and Decode Strings - walkthrough

**Difficulty:** Medium &middot; **Module:** 01 Arrays Hashing

## Brief

Design an algorithm to encode a list of strings into a single string. The encoded string is then decoded back to the original list of strings. The encoding must handle strings containing any characters, including the delimiter.

## Examples

- `['hello','world']` &rarr; `['hello','world']`
- `['', '']` &rarr; `['', '']`
- `['a#b', 'c']` &rarr; `['a#b', 'c']`

## Constraints

- 0 <= len(strs) <= 200
- 0 <= len(strs[i]) <= 200
- Strings may contain any ASCII characters

## Intuition

We need a delimiter that **cannot appear in the data**. If we *length-prefix*
each string, the delimiter can be anything (we never need to look for it in
the data).

## Approach
Encoder: for each `s`, append `len(s) + '#' + s`.
Decoder: read digits until '#' to learn the length, then read exactly that
many characters.

## Complexity
- **Time:** O(n) where n is the total length of all strings.
- **Space:** O(n) for the output.

## Why not a non-printable delimiter?
A non-printable character (e.g. `\u0001`) *does* work in some contexts, but
the input strings may legally contain *any* character. Length-prefixing is
robust.

## Follow-ups
- *Streaming decode?* Stateful — you need to know when one string ends and
  the next begins. The length-prefix approach streams cleanly: read length,
  read that many bytes.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

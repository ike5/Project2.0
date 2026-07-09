# Encode and Decode Strings

**Difficulty:** Medium

## Problem

Design an algorithm to encode a list of strings into a single string. The encoded string is then decoded back to the original list of strings. The encoding must handle strings containing any characters, including the delimiter.

## Examples

```
Input:  ['hello','world']
Output: ['hello','world']
```

```
Input:  ['', '']
Output: ['', '']
```

```
Input:  ['a#b', 'c']
Output: ['a#b', 'c']
```

## Constraints

- 0 <= len(strs) <= 200
- 0 <= len(strs[i]) <= 200
- Strings may contain any ASCII characters

## Hints

1. Length-prefix the encoding: store `<len>#<s>` for each string.
2. Walk the encoded string and read until '#' to find each length.

## Solution

See [`../../solutions/08-encode-and-decode-strings/`](../../solutions/08-encode-and-decode-strings/) for the Python and Java 21 solutions and a step-by-step walkthrough.

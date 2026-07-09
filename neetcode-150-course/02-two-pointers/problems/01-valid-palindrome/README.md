# Valid Palindrome

**Difficulty:** Easy

## Problem

Given a string `s`, return `True` if it is a palindrome after converting all uppercase letters to lowercase and removing all non-alphanumeric characters.

## Examples

```
Input:  s = 'A man, a plan, a canal: Panama'
Output: True
```

```
Input:  s = 'race a car'
Output: False
```

```
Input:  s = ' '
Output: True
```

## Constraints

- 1 <= len(s) <= 2 * 10^5
- s consists of printable ASCII characters

## Hints

1. Two pointers from opposite ends.
2. Skip non-alphanumeric chars and compare lowercased values.

## Solution

See [`../../solutions/01-valid-palindrome/`](../../solutions/01-valid-palindrome/) for the Python and Java 21 solutions and a step-by-step walkthrough.

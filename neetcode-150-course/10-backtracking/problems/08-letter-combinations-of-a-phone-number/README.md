# Letter Combinations of a Phone Number

**Difficulty:** Medium

## Problem

Given a string containing digits from 2-9 inclusive, return all possible letter combinations that the number could represent. Return the answer in **any order**. A mapping of digit to letters (just like on the telephone buttons) is given below. Note that 1 does not map to any letters.

## Examples

```
Input:  digits = '23'
Output: ['ad','ae','af','bd','be','bf','cd','ce','cf']
```

```
Input:  digits = ''
Output: []
```

```
Input:  digits = '2'
Output: ['a','b','c']
```

## Constraints

- 0 <= len(digits) <= 4
- digits[i] is a digit in the range ['2', '9']

## Hints

1. Backtrack. At each digit, try all its letters.

## Solution

See [`../../solutions/08-letter-combinations-of-a-phone-number/`](../../solutions/08-letter-combinations-of-a-phone-number/) for the Python and Java 21 solutions and a step-by-step walkthrough.

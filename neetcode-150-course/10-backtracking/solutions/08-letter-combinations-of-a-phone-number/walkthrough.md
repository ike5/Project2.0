# Letter Combinations of a Phone Number - walkthrough

**Difficulty:** Medium &middot; **Module:** 10 Backtracking

## Brief

Given a string containing digits from 2-9 inclusive, return all possible letter combinations that the number could represent. Return the answer in **any order**. A mapping of digit to letters (just like on the telephone buttons) is given below. Note that 1 does not map to any letters.

## Examples

- `digits = '23'` &rarr; `['ad','ae','af','bd','be','bf','cd','ce','cf']`
- `digits = ''` &rarr; `[]`
- `digits = '2'` &rarr; `['a','b','c']`

## Constraints

- 0 <= len(digits) <= 4
- digits[i] is a digit in the range ['2', '9']

## Intuition

Backtrack. For each digit, try its letters. The empty input
returns an empty list.

**Time:** O(4^n) where n is the number of digits (4 because '7' and '9'
have 4 letters). **Space:** O(n) recursion.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

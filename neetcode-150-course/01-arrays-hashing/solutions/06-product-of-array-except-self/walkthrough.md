# Product of Array Except Self - walkthrough

**Difficulty:** Medium &middot; **Module:** 01 Arrays Hashing

## Brief

Given an integer array `nums`, return an array `answer` such that `answer[i]` equals the product of all the elements of `nums` except `nums[i]`. Solve it in O(n) time without using the division operator.

## Examples

- `nums = [1,2,3,4]` &rarr; `[24,12,8,6]`
- `nums = [-1,1,0,-3,3]` &rarr; `[0,0,9,0,0]`

## Constraints

- 2 <= len(nums) <= 10^5
- -30 <= nums[i] <= 30
- The product of any prefix or suffix fits in a 32-bit int

## Intuition

For each `i`, the answer is `(product of all elements to the left) * (product
of all elements to the right)`.

## Approach
Two passes, O(1) extra space (the output array counts as output).
1. **Forward pass**: fill `answer[i]` with the product of `nums[0..i-1]`.
2. **Backward pass**: maintain a running suffix product and multiply it into
   `answer[i]`.

## Complexity
- **Time:** O(n).
- **Space:** O(1) extra (the output doesn't count).

## Follow-ups
- *What if the input can have zeros and the problem allowed division?*
  Compute the total product, divide by each `nums[i]`, but replace the
  result with 0 for any `nums[i] == 0`. Handle multiple zeros: every
  answer is 0.
- *64-bit values?* Use `long` in Java or check constraints.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21

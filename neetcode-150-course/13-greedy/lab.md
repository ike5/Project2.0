# Lab 13 — Greedy

**You'll:** implement *Maximum Subarray* (Kadane) and *Jump Game* in both
languages. ⏱️ ~1 h.

---

## Part A — *Maximum Subarray* in Python

```python
def max_subarray(nums):
    best = cur = nums[0]
    for x in nums[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best


if __name__ == "__main__":
    assert max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6
    assert max_subarray([1]) == 1
    assert max_subarray([5, 4, -1, 7, 8]) == 23
    print("all tests passed")
```

`cur` is the best sum of any subarray **ending at the current index**.
Either extend the previous best or start fresh.

## Part B — *Maximum Subarray* in Java 21

```java
public class LabMaxSubarray {
    public static int maxSubarray(int[] nums) {
        int best = nums[0], cur = nums[0];
        for (int i = 1; i < nums.length; i++) {
            cur = Math.max(nums[i], cur + nums[i]);
            best = Math.max(best, cur);
        }
        return best;
    }

    public static void main(String[] args) {
        assert maxSubarray(new int[]{-2, 1, -3, 4, -1, 2, 1, -5, 4}) == 6;
        assert maxSubarray(new int[]{1}) == 1;
        assert maxSubarray(new int[]{5, 4, -1, 7, 8}) == 23;
        System.out.println("all tests passed");
    }
}
```

## Part C — *Jump Game* in Python

```python
def can_jump(nums):
    farthest = 0
    for i, x in enumerate(nums):
        if i > farthest:
            return False
        farthest = max(farthest, i + x)
    return True


if __name__ == "__main__":
    assert can_jump([2, 3, 1, 1, 4]) is True
    assert can_jump([3, 2, 1, 0, 4]) is False
    assert can_jump([0]) is True
    print("all tests passed")
```

`farthest` is the rightmost index we can reach. If at any point `i`
exceeds it, we're stuck.

## Part D — *Jump Game* in Java 21

```java
public class LabJumpGame {
    public static boolean canJump(int[] nums) {
        int farthest = 0;
        for (int i = 0; i < nums.length; i++) {
            if (i > farthest) return false;
            farthest = Math.max(farthest, i + nums[i]);
        }
        return true;
    }

    public static void main(String[] args) {
        assert canJump(new int[]{2, 3, 1, 1, 4});
        assert !canJump(new int[]{3, 2, 1, 0, 4});
        assert canJump(new int[]{0});
        System.out.println("all tests passed");
    }
}
```

## What you learned

- **Kadane's** is the standard O(n) solution for the maximum-subarray
  problem.
- **Greedy reachability** is a common pattern: track the farthest
  reachable position and check if the goal is in it.

➡️ **[challenge.md](./challenge.md)**

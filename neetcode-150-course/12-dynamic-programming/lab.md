# Lab 12 — Dynamic Programming

**You'll:** implement *Climbing Stairs* and *House Robber* in both
languages, getting comfortable with the 1D rolling DP pattern. ⏱️ ~1.5 h.

---

## Part A — *Climbing Stairs* in Python

```python
def climb_stairs(n):
    if n <= 2: return n
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b


if __name__ == "__main__":
    assert climb_stairs(2) == 2
    assert climb_stairs(3) == 3
    assert climb_stairs(5) == 8
    print("all tests passed")
```

`dp[i] = dp[i-1] + dp[i-2]` — the Fibonacci recurrence. We keep only
the last two values.

## Part B — *Climbing Stairs* in Java 21

```java
public class LabClimbStairs {
    public static int climbStairs(int n) {
        if (n <= 2) return n;
        int a = 1, b = 2;
        for (int i = 3; i <= n; i++) {
            int tmp = a + b;
            a = b;
            b = tmp;
        }
        return b;
    }

    public static void main(String[] args) {
        assert climbStairs(2) == 2;
        assert climbStairs(3) == 3;
        assert climbStairs(5) == 8;
        System.out.println("all tests passed");
    }
}
```

## Part C — *House Robber* in Python

```python
def rob(nums):
    if not nums: return 0
    if len(nums) == 1: return nums[0]
    a, b = nums[0], max(nums[0], nums[1])
    for i in range(2, len(nums)):
        a, b = b, max(b, a + nums[i])
    return b


if __name__ == "__main__":
    assert rob([1, 2, 3, 1]) == 4
    assert rob([2, 7, 9, 3, 1]) == 12
    assert rob([2, 1, 1, 2]) == 4
    print("all tests passed")
```

`dp[i] = max(dp[i-1], dp[i-2] + nums[i])` — either we skip house `i` or
we rob it.

## Part D — *House Robber* in Java 21

```java
public class LabHouseRobber {
    public static int rob(int[] nums) {
        if (nums.length == 0) return 0;
        if (nums.length == 1) return nums[0];
        int a = nums[0], b = Math.max(nums[0], nums[1]);
        for (int i = 2; i < nums.length; i++) {
            int tmp = b;
            b = Math.max(b, a + nums[i]);
            a = tmp;
        }
        return b;
    }

    public static void main(String[] args) {
        assert rob(new int[]{1, 2, 3, 1}) == 4;
        assert rob(new int[]{2, 7, 9, 3, 1}) == 12;
        assert rob(new int[]{2, 1, 1, 2}) == 4;
        System.out.println("all tests passed");
    }
}
```

## What you learned

- **1D rolling DP.** Keep the last two values; update in place.
- **Recurrence design.** `dp[i] = something with dp[i-1] and dp[i-2]`
  → Fibonacci-style. `dp[i] = max(dp[i-1], dp[i-2] + x[i])` → rob/skip.

➡️ **[challenge.md](./challenge.md)**

# Lab 05 — Binary Search

**You'll:** implement *Binary Search* and *Search a 2D Matrix* in both
languages, paying attention to the integer-arithmetic gotchas. ⏱️ ~1 h.

---

## Part A — *Binary Search* in Python

```python
def search(nums, target):
    ...


if __name__ == "__main__":
    assert search([-1, 0, 3, 5, 9, 12], 9) == 4
    assert search([-1, 0, 3, 5, 9, 12], 2) == -1
    assert search([5], 5) == 0
    assert search([1, 2, 3, 4, 5], 6) == -1
    print("all tests passed")
```

**Walk-through:**

```python
def search(nums: list[int], target: int) -> int:
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
```

Note `lo + (hi - lo) // 2` — in Python this is the same as `(lo + hi) // 2`,
but the form we use in Java avoids overflow. **In Python it's a style
choice; in Java it's correctness.**

✅ Run it.

## Part B — *Binary Search* in Java 21

```java
public class LabSearch {
    public static int search(int[] nums, int target) {
        // your code
    }

    public static void main(String[] args) {
        assert search(new int[]{-1, 0, 3, 5, 9, 12}, 9) == 4;
        assert search(new int[]{-1, 0, 3, 5, 9, 12}, 2) == -1;
        assert search(new int[]{5}, 5) == 0;
        assert search(new int[]{1, 2, 3, 4, 5}, 6) == -1;
        System.out.println("all tests passed");
    }
}
```

**Walk-through:**

```java
public static int search(int[] nums, int target) {
    int lo = 0, hi = nums.length - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (nums[mid] == target) return mid;
        if (nums[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}
```

The `/` on two `int`s is **integer division** in Java — no cast needed.
But `(lo + hi) / 2` would overflow if both were near 2^31. So we use
`lo + (hi - lo) / 2`.

## Part C — *Search a 2D Matrix* in Python

```python
def search_matrix(matrix, target):
    ...


if __name__ == "__main__":
    m = [[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]]
    assert search_matrix(m, 3) is True
    assert search_matrix(m, 13) is False
    print("all tests passed")
```

**Walk-through:** treat the matrix as a flat array.

```python
def search_matrix(matrix: list[list[int]], target: int) -> bool:
    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    lo, hi = 0, m * n - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        v = matrix[mid // n][mid % n]
        if v == target:
            return True
        if v < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return False
```

`mid // n` is the row, `mid % n` is the column.

## Part D — *Search a 2D Matrix* in Java 21

```java
public class LabSearchMatrix {
    public static boolean searchMatrix(int[][] matrix, int target) {
        // your code
    }

    public static void main(String[] args) {
        int[][] m = {
            {1, 3, 5, 7},
            {10, 11, 16, 20},
            {23, 30, 34, 60}
        };
        assert searchMatrix(m, 3);
        assert !searchMatrix(m, 13);
        System.out.println("all tests passed");
    }
}
```

```java
public static boolean searchMatrix(int[][] matrix, int target) {
    if (matrix.length == 0 || matrix[0].length == 0) return false;
    int m = matrix.length, n = matrix[0].length;
    int lo = 0, hi = m * n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        int v = matrix[mid / n][mid % n];
        if (v == target) return true;
        if (v < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return false;
}
```

## What you learned

- **The two templates** (exact match vs. search on answer).
- **The `lo + (hi - lo) / 2` idiom** for safe integer midpoint.
- **Flat-indexing a 2D matrix** when the rows are sorted in chain.

➡️ **[challenge.md](./challenge.md)** then the [problems/](./problems/) in order.

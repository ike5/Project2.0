# Lab 02 — Two Pointers

**You'll:** solve *Valid Palindrome* and *Two Sum II* in both languages from
scratch, comparing how each language handles the "skip non-alphanumeric" and
"advance the right pointer" steps. ⏱️ ~1 h.

---

## Part A — *Valid Palindrome* in Python

Create `02-two-pointers/lab_valid_palindrome.py`:

```python
def is_palindrome(s: str) -> bool:
    ...


if __name__ == "__main__":
    assert is_palindrome("A man, a plan, a canal: Panama") is True
    assert is_palindrome("race a car") is False
    assert is_palindrome(" ") is True
    assert is_palindrome("a") is True
    assert is_palindrome("ab") is False
    print("all tests passed")
```

**Walk-through:**

```python
def is_palindrome(s: str) -> bool:
    l, r = 0, len(s) - 1
    while l < r:
        # skip non-alphanumeric on the left
        while l < r and not s[l].isalnum():
            l += 1
        # skip non-alphanumeric on the right
        while l < r and not s[r].isalnum():
            r -= 1
        if s[l].lower() != s[r].lower():
            return False
        l += 1
        r -= 1
    return True
```

Key points:

- `s[l].isalnum()` is the right Python primitive for "letter or digit."
- We check `l < r` *inside* the skip loops so we don't walk off the end of
  a string like `"!!!"` (which has no alphanumerics at all).
- We compare *lowercased* values. `'A'.lower() == 'a'.lower()`.

✅ Run it.

## Part B — *Valid Palindrome* in Java 21

Create `02-two-pointers/LabValidPalindrome.java`:

```java
public class LabValidPalindrome {
    public static boolean isPalindrome(String s) {
        // your code
    }

    public static void main(String[] args) {
        assert isPalindrome("A man, a plan, a canal: Panama");
        assert !isPalindrome("race a car");
        assert isPalindrome(" ");
        assert isPalindrome("a");
        assert !isPalindrome("ab");
        System.out.println("all tests passed");
    }
}
```

**Walk-through:**

```java
public static boolean isPalindrome(String s) {
    int l = 0, r = s.length() - 1;
    while (l < r) {
        while (l < r && !Character.isLetterOrDigit(s.charAt(l))) l++;
        while (l < r && !Character.isLetterOrDigit(s.charAt(r))) r--;
        if (Character.toLowerCase(s.charAt(l)) !=
            Character.toLowerCase(s.charAt(r))) return false;
        l++;
        r--;
    }
    return true;
}
```

Notes:
- `Character.isLetterOrDigit(char)` is the Java equivalent of Python's
  `s[i].isalnum()`. It returns `true` for `[A-Za-z0-9]`.
- `Character.toLowerCase(char)` returns a `char`, not a `String`.
- We compare `char` values with `==` after both sides have been lowercased.

✅ Compile and run.

## Part C — *Two Sum II* in Python

```python
def two_sum_sorted(numbers, target):
    ...


if __name__ == "__main__":
    assert two_sum_sorted([2, 7, 11, 15], 9) == [1, 2]
    assert two_sum_sorted([2, 3, 4], 6) == [1, 3]
    assert two_sum_sorted([-1, 0], -1) == [1, 2]
    print("all tests passed")
```

**Walk-through:**

```python
def two_sum_sorted(numbers: list[int], target: int) -> list[int]:
    l, r = 0, len(numbers) - 1
    while l < r:
        s = numbers[l] + numbers[r]
        if s == target:
            return [l + 1, r + 1]   # 1-indexed
        if s < target:
            l += 1
        else:
            r -= 1
    return []
```

Why this works: if the sum is too small, the *only* way to increase it
monotonically is to move `l` right (we discard the too-small left value).
Symmetrically for too-large.

## Part D — *Two Sum II* in Java 21

```java
public class LabTwoSumSorted {
    public static int[] twoSumSorted(int[] numbers, int target) {
        // your code
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(twoSumSorted(new int[]{2, 7, 11, 15}, 9)));
        System.out.println(Arrays.toString(twoSumSorted(new int[]{2, 3, 4}, 6)));
        System.out.println(Arrays.toString(twoSumSorted(new int[]{-1, 0}, -1)));
    }
}
```

**Walk-through:** the same as the Python version, but:

- Method returns `int[]`. Print with `Arrays.toString`.
- 1-indexing: `new int[] { l + 1, r + 1 }`.

## What you learned

- **The opposite-ends template:** `l = 0, r = n - 1, while l < r, decide which
  side to move`.
- **Why sorting enables two pointers:** sorted means monotone — moving one
  pointer only ever increases (or decreases) the comparison.
- **Language differences:** Python's `str.isalnum()` vs Java's
  `Character.isLetterOrDigit(char)`. Python's `.lower()` vs Java's
  `Character.toLowerCase(char)`. Both return the same result on ASCII.

➡️ **[challenge.md](./challenge.md)** then the [problems/](./problems/) in order.

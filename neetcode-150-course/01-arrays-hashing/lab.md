# Lab 01 — Arrays & Hashing

**You'll:** solve *Contains Duplicate* and *Valid Anagram* in both languages
from scratch, comparing the idioms side by side. ⏱️ ~1.5 h.

---

## Part A — *Contains Duplicate* in Python

Create a file `01-arrays-hashing/lab_contains_duplicate.py` (don't peek at
`solutions/01-contains-duplicate/` until you've tried).

```python
def contains_duplicate(nums: list[int]) -> bool:
    ...


if __name__ == "__main__":
    assert contains_duplicate([1, 2, 3, 1]) is True
    assert contains_duplicate([1, 2, 3, 4]) is False
    assert contains_duplicate([1, 1, 1, 3, 3, 4, 3, 2, 4, 2]) is True
    assert contains_duplicate([]) is False
    print("all tests passed")
```

**Walk-through:**

1. Create an empty `set` named `seen`.
2. For each `x` in `nums`:
   - If `x in seen`, return `True`.
   - Otherwise, `seen.add(x)`.
3. After the loop, return `False`.

Why a set and not a list? `x in set` is O(1); `x in list` is O(n). The set
gives you a single-pass O(n) solution.

✅ Run `python 01-arrays-hashing/lab_contains_duplicate.py` — should print
`all tests passed`.

## Part B — *Contains Duplicate* in Java 21

Create `01-arrays-hashing/lab_contains_duplicate.java`:

```java
import java.util.HashSet;
import java.util.Set;

public class LabContainsDuplicate {
    public static boolean containsDuplicate(int[] nums) {
        // your code
    }

    public static void main(String[] args) {
        assert containsDuplicate(new int[]{1, 2, 3, 1});
        assert !containsDuplicate(new int[]{1, 2, 3, 4});
        assert containsDuplicate(new int[]{1, 1, 1, 3, 3, 4, 3, 2, 4, 2});
        assert !containsDuplicate(new int[]{});
        System.out.println("all tests passed");
    }
}
```

**Walk-through:** the same logic, but in Java:

```java
public static boolean containsDuplicate(int[] nums) {
    Set<Integer> seen = new HashSet<>();
    for (int x : nums) {
        if (!seen.add(x)) return true;     // add() returns false on duplicate
    }
    return false;
}
```

✅ Compile and run:
```bash
mkdir -p /tmp/out
javac -d /tmp/out 01-arrays-hashing/lab_contains_duplicate.java
java -ea -cp /tmp/out LabContainsDuplicate
```

> The `-ea` flag enables `assert` checks at runtime. Without it, `assert`
> statements are stripped out.

## Part C — Compare

Look at both implementations side by side. Note:

- **Python:** `if x in seen: return True; seen.add(x)`. Two operations.
- **Java:**  `if (!seen.add(x)) return true;` — a single operation, because
  `HashSet.add` returns `false` when the element was already present.
- The Java code is *slightly* more compact for this specific case because
  the standard library's API was designed for it.

## Part D — *Valid Anagram* in Python

Create `01-arrays-hashing/lab_valid_anagram.py`:

```python
def is_anagram(s: str, t: str) -> bool:
    ...


if __name__ == "__main__":
    assert is_anagram("anagram", "nagaram") is True
    assert is_anagram("rat", "car") is False
    assert is_anagram("a", "a") is True
    assert is_anagram("ab", "a") is False
    assert is_anagram("", "") is True
    print("all tests passed")
```

**Walk-through (shortest):**

```python
from collections import Counter
return Counter(s) == Counter(t)
```

A `Counter` is a `dict` subclass that maps each unique element to its count.
Two Counters are equal iff every element appears the same number of times in
both — exactly the definition of an anagram.

✅ Run the script. All asserts should pass.

## Part E — *Valid Anagram* in Java 21

Create `01-arrays-hashing/lab_valid_anagram.java`:

```java
public class LabValidAnagram {
    public static boolean isAnagram(String s, String t) {
        // your code
    }

    public static void main(String[] args) {
        assert isAnagram("anagram", "nagaram");
        assert !isAnagram("rat", "car");
        assert isAnagram("a", "a");
        assert !isAnagram("ab", "a");
        assert isAnagram("", "");
        System.out.println("all tests passed");
    }
}
```

**Walk-through (using a `int[26]`):**

```java
public static boolean isAnagram(String s, String t) {
    if (s.length() != t.length()) return false;
    int[] count = new int[26];
    for (int i = 0; i < s.length(); i++) {
        count[s.charAt(i) - 'a']++;
        count[t.charAt(i) - 'a']--;
    }
    for (int c : count) if (c != 0) return false;
    return true;
}
```

We don't even need two separate loops: increment for `s`, decrement for `t`,
and the array is all zeros iff `s` and `t` are anagrams. This is O(n) and
O(1) extra space.

> **If you need Unicode:** replace `int[26]` with `Map<Character,Integer>`,
> but the algorithm is the same.

✅ Compile and run:
```bash
javac -d /tmp/out 01-arrays-hashing/lab_valid_anagram.java
java -ea -cp /tmp/out LabValidAnagram
```

## Part F — Compare the two

| | Python | Java |
|---|--------|------|
| One-liner | `Counter(s) == Counter(t)` | not really — need a `int[26]` or stream |
| Pure stdlib | yes | yes (no `Counter` in `java.util`) |
| Time | O(n) | O(n) |
| Space | O(k) where k = distinct chars | O(1) (always 26) |

Java's `int[26]` is faster for ASCII lowercase because it's a tight array
loop. Python's `Counter` is more general (works on any hashable).

## What you learned

- **Set membership** is O(1) in both languages. The basic building block.
- **Frequency counts** via `Counter` (Python) or `int[26]` / `Map<K,Integer>`
  (Java). The right tool depends on the input.
- **Idiom differences:** `set.add` returning `false` on duplicate is the
  Java-idiomatic way to detect "is already present?". Python prefers the
  more explicit `if x in seen`.
- **Compile-and-run in Java:** every solution is a single public class with
  a `main` method, compiled to a destination directory and run with the
  classpath set to that directory.

➡️ **[challenge.md](./challenge.md)** then start the [problems/](./problems/)
in order.

# Solution 00 — Setup & Orientation

Reference answers for the four tasks. Try the lab and challenge first; only
peek if you're stuck.

## Key points

### Task 1 — Python `is_palindrome`

The standard two-pointer trick: skip non-alphanumerics, compare lowercased
chars. Runs in O(n) time, O(1) extra space.

```python
def is_palindrome(s: str) -> bool:
    l, r = 0, len(s) - 1
    while l < r:
        while l < r and not s[l].isalnum():
            l += 1
        while l < r and not s[r].isalnum():
            r -= 1
        if s[l].lower() != s[r].lower():
            return False
        l += 1
        r -= 1
    return True
```

In `main`:

```python
print(f"is_palindrome('A man, a plan, a canal: Panama') -> {is_palindrome('A man, a plan, a canal: Panama')}")
print(f"is_palindrome('race a car')                       -> {is_palindrome('race a car')}")
print(f"is_palindrome(' ')                                -> {is_palindrome(' ')}")
```

Expected: `True`, `False`, `True`.

### Task 2 — Java `isPalindrome`

```java
public static boolean isPalindrome(String s) {
    int l = 0, r = s.length() - 1;
    while (l < r) {
        while (l < r && !Character.isLetterOrDigit(s.charAt(l))) l++;
        while (l < r && !Character.isLetterOrDigit(s.charAt(r))) r--;
        if (Character.toLowerCase(s.charAt(l)) != Character.toLowerCase(s.charAt(r))) {
            return false;
        }
        l++;
        r--;
    }
    return true;
}
```

In `main`:

```java
System.out.println("is_palindrome('A man, a plan, a canal: Panama') -> " + isPalindrome("A man, a plan, a canal: Panama"));
System.out.println("is_palindrome('race a car')                       -> " + isPalindrome("race a car"));
System.out.println("is_palindrome(' ')                                -> " + isPalindrome(" "));
```

### Task 3 — Time complexity comment

Both files: `# Time complexity: O(n)` / `// Time complexity: O(n)`.

## Common pitfalls

- **Forgetting to lowercase.** `"A"` and `"a"` are different in Java's `==`,
  different in Python's `==` too. Always `lower()` (Python) or
  `Character.toLowerCase` (Java).
- **Forgetting to skip non-alphanumerics.** `isalnum()` / `Character.isLetterOrDigit`
  is the right primitive.
- **Java's `String.charAt` doesn't throw on ASCII**, but does for some
  surrogate-pair edge cases. For interview problems you can ignore that
  subtlety.
- **Re-compiling Java.** The compiler re-reads the `.java` file; you don't
  need to delete `out/` between runs.

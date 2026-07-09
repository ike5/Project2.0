# Challenge 00 — Setup & Orientation

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Python: add a function.** Edit `00-setup/code/hello_neetcode.py` and add a
   function `is_palindrome(s: str) -> bool` that returns `True` iff `s` reads
   the same forwards and backwards (ignoring case and non-alphanumeric chars).
   Then add three lines to `main()` that print the result for `"A man, a plan,
   a canal: Panama"`, `"race a car"`, and `" "` (a single space — should be
   `True`).
2. **Java: add a method.** Add the same `isPalindrome(String s)` static method
   to `HelloNeetCode.java` and three corresponding `System.out.println` calls
   to `main`.
3. **Run both.** Confirm both produce the same output.
4. **Time complexity.** In a comment at the top of each file, write the
   time complexity of `is_palindrome` / `isPalindrome`. (It should be O(n).)

## Success criteria

- [ ] `python 00-setup/code/hello_neetcode.py` prints the three palindrome
  results correctly.
- [ ] `java -cp /tmp/out HelloNeetCode` prints the same three results.
- [ ] The complexity comment is present in both files.

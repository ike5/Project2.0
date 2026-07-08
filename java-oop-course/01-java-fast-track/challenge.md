# Challenge 01 — Language Essentials

Solution in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Reference aliasing bug.** Write a method
   `List<Integer> addOne(List<Integer> xs)` that *intends* to return a new
   list with 1 added to each element, but accidentally mutates the caller's
   list. Demonstrate the bug, then fix it so the original list is untouched.
   (Hint: a stream pipeline is the cleanest fix.)

2. **Null-safe lookup.** Given `Map<String, String> config`, write a method
   `String getOrDefault(Map<String, String> config, String key, String fallback)`
   that never throws on a missing key and never returns `null`. Use
   `Map.getOrDefault` or `Map.containsKey` + `Map.get`.

3. **Classify with a switch expression.** Write
   `String grade(int score)` using a switch expression: `< 0` or `> 100` →
   `"invalid"`, `>= 90` → `"A"`, `>= 80` → `"B"`, `>= 70` → `"C"`, else
   `"F"`.

4. **Pattern matching.** Write `String describe(Object o)` that returns
   `"int: <n>"` for `Integer`, `"string: <s>"` for `String`,
   `"list: <size>"` for `List<?>`, `"null"` for `null`, and
   `"unknown: <class>"` otherwise. Use pattern matching for `instanceof`.

## Success criteria

- [ ] You reproduced and fixed the list-mutation aliasing bug.
- [ ] `getOrDefault` is null-safe and exception-free.
- [ ] `grade` handles invalid ranges and all bands.
- [ ] `describe` covers all four cases using `instanceof` pattern matching
      (no explicit cast).

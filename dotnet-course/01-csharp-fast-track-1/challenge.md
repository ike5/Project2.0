# Challenge 01 — Types & Null Safety

Solution in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Reference aliasing bug.** Write a method `void AddTax(List<decimal> prices)` that
   *intends* to return a new list with 10% tax but accidentally mutates the caller's
   list. Demonstrate the bug, then fix it so the original list is untouched.

2. **Null-safe lookup.** Given `Dictionary<string,string> config`, write a method
   `string GetOrDefault(string key, string fallback)` that never throws on a missing
   key and never returns null. Use `TryGetValue`.

3. **Classify with patterns.** Write `string Grade(int score)` using a `switch`
   expression: `<0 or >100` → "invalid", `>=90` → "A", `>=80` → "B", `>=70` → "C",
   else "F".

4. **NRT discipline.** Take this and make the compiler warning-free *without* using
   `!`: `string FirstWord(string? sentence)` returning the first whitespace-delimited
   word, or `"(empty)"` if the input is null/blank.

## Success criteria
- [ ] You reproduced and fixed the list-mutation aliasing bug.
- [ ] `GetOrDefault` is null-safe and exception-free.
- [ ] `Grade` handles invalid ranges and all bands.
- [ ] `FirstWord` compiles with zero nullable warnings and no `!`.

# Challenge 04 — Foundation Katas

Add these to **FoundationKata** with tests (`swift test`). Solution in
[`solutions/`](./solutions/).

## Tasks
1. **Relative date.** `Dates.relativeString(from:to:)` returning e.g. "in 3 days" /
   "2 days ago" using `RelativeDateTimeFormatter` (or your own logic from
   `daysBetween`). Test a couple of fixed dates.

2. **Slugify.** `TextStats.slug(_:)` that lowercases, trims, and replaces runs of
   non-alphanumerics with single hyphens (`"  Hello, World! "` → `"hello-world"`).

3. **Bytes formatter.** `format(bytes:)` returning a human size ("1.5 MB") using
   `ByteCountFormatter` (or manual). Test 1500 and 1_500_000.

4. **Money parsing.** Parse a currency string like `"$1,234.50"` into a `Decimal`
   (strip grouping/symbol) and back to a formatted string with 2 fraction digits.
   Explain why `Decimal`/`NSDecimalNumber` is preferred over `Double` for money.

## Success criteria
- [ ] Relative date strings are correct for past/future.
- [ ] `slug` collapses punctuation/whitespace to single hyphens.
- [ ] Byte formatting is human-readable and tested.
- [ ] Money round-trips via `Decimal`; you can justify avoiding `Double`.

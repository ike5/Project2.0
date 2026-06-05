# Challenge 01 — Swift Fluency

Solution in [`solutions/`](./solutions/). Try first. Everything here is runnable with
`swift yourfile.swift`.

## Tasks
1. **Protocol + default + conformance.** Define `protocol Summable { static func +(a: Self, b: Self) -> Self; static var zero: Self { get } }` and a generic `func total<T: Summable>(_ xs: [T]) -> T`. Conform `Int` and `Double` and total a list of each.

2. **Optional pipeline.** Write `func firstEven(_ xs: [Int]) -> Int?` using `first(where:)`, then print its result with a default via `??` for both a matching and non-matching array — no force-unwraps.

3. **Result-style error handling.** Write `func parsePort(_ s: String) -> Result<Int, String>` returning `.success` for a valid 1–65535 integer and `.failure(message)` otherwise. Pattern-match the result to print.

4. **Break a retain cycle.** Create a `Timer`-like callback class where a closure captures `self`. Show the leak (no `deinit`), then fix it with `[weak self]` and show `deinit` firing.

5. **Stretch:** Implement a `@propertyWrapper` `Capitalized` that upper-cases the first letter on set, and use it on a struct's `name` property.

## Success criteria
- [ ] Generic `total` works for `[Int]` and `[Double]` via the protocol.
- [ ] `firstEven` handles match/no-match with no force-unwrap.
- [ ] `parsePort` returns `Result` and you pattern-match both cases.
- [ ] You demonstrated and then fixed a closure retain cycle with `[weak self]`.

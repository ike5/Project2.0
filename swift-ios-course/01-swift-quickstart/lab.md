# Lab 01 — Swift in Anger (command line)

**You'll:** exercise the core language features and *see* ARC deallocation — all from a
single runnable script. ⏱️ ~35 min. No Xcode UI needed.

---

## Part A — Run the scratch script
```bash
cd swift-ios-course/01-swift-quickstart/code
swift scratch.swift
```
✅ Expected output (roughly):
```
struct copy -> first stays: 0 | b0.x: 0
class shares -> c.x: 9
optional default: -1
loaded: places
doubled evens sum: 12
try? on failure: nil
deinit X
deinit Y
end of demo
```
Read [`scratch.swift`](./code/scratch.swift) line by line and match each print to a
concept from the README.

## Part B — Prove value vs reference yourself
Add to the script:
```swift
struct Counter { var n = 0; mutating func inc() { n += 1 } }
var c1 = Counter(); var c2 = c1; c2.inc()
print("c1.n=\(c1.n) c2.n=\(c2.n)")   // c1.n=0 c2.n=1  (struct copied)
```
Re-run. ✅ The copy is independent — note `mutating` is required to change `self` in a
struct method.

## Part C — Watch a retain cycle leak
Add a deliberately cyclic version and observe the **missing** `deinit`:
```swift
final class Pet { var owner: Person?; deinit { print("deinit Pet") } }
final class Person { var pet: Pet?; deinit { print("deinit Person") } }
do {
    let p = Person(); let a = Pet()
    p.pet = a; a.owner = p          // STRONG cycle -> neither deallocates
}
print("after scope")
```
Re-run. ✅ You will **not** see "deinit Pet"/"deinit Person" — that's a leak. Now break it:
change `var owner: Person?` to `weak var owner: Person?` and re-run → both `deinit`s print.

> This is the #1 memory bug in Cocoa apps, and exactly why **delegates are `weak`**.

## Part D — Enums & exhaustive switch
Add an enum modeling a network result and a `switch` that the compiler forces you to
handle completely:
```swift
enum Fetch<T> { case ok(T), empty, error(String) }
func handle(_ f: Fetch<[Int]>) -> String {
    switch f {
    case .ok(let xs) where xs.isEmpty: return "ok but empty"
    case .ok(let xs): return "ok \(xs.count)"
    case .empty: return "empty"
    case .error(let m): return "error \(m)"
    }
}
print(handle(.ok([1,2,3])))   // ok 3
```
✅ Remove a `case` and the compiler errors — exhaustiveness is enforced.

## What you learned
- Structs copy; classes share (ARC); `mutating` for struct methods.
- Optionals, enums with associated values + exhaustive `switch`, closures.
- Retain cycles leak; `weak` breaks them — the basis for `weak` delegates.

➡️ **[challenge.md](./challenge.md)** then [Module 02](../02-swiftui-fundamentals/).

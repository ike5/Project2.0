# Module 01 — Swift Quick-Start

**Goal:** get fluent fast in the Swift features that matter for iOS — framed as deltas
from C#. You know some Swift, so this is brisk; the focus is on what differs and on
**ARC** (which ties to the Objective-C heritage). ⏱️ ~1.5 h · 🎯 Prereq: 00.

> Full reference: [cheatsheets/swift-syntax.md](../cheatsheets/swift-syntax.md).

---

## 1. Value vs reference types (the big one)

```swift
struct PointS { var x = 0 }      // value type: copied
class  PointC { var x = 0 }      // reference type: shared, ARC-managed

var a = PointS(); var b = a; b.x = 9     // a.x == 0  (copy)
let c = PointC(); let d = c; d.x = 9     // c.x == 9  (same object)
```
Swift leans on **value types** (`struct`/`enum`) far more than C#. SwiftUI views and most
models are structs. Use `class` for identity, shared mutable state, or Obj-C interop.

## 2. Optionals (no nulls)

```swift
var name: String? = nil
if let name { print(name) }              // shorthand unwrap (Swift 5.7+)
guard let name else { return }           // early-exit unwrap
let n = name?.count ?? 0                  // chaining + default
```
Avoid `!` force-unwrap except when a value is guaranteed.

## 3. Protocols & protocol-oriented design

```swift
protocol Drawable { func draw() -> String }
extension Drawable { func draw() -> String { "•" } }   // default implementation
struct Dot: Drawable {}
extension Array where Element == Int { var total: Int { reduce(0, +) } }  // constrained ext.
```
Swift favors small protocols + extensions over deep class hierarchies (vs C# interfaces +
inheritance).

## 4. Enums with associated values & pattern matching

```swift
enum Loadable<T> {
    case idle, loading
    case loaded(T)
    case failed(Error)
}
switch state {
case .loaded(let value): show(value)
case .failed(let error): report(error)
default: break
}
```
Far richer than C# enums — they carry data and drive exhaustive `switch`.

## 5. Closures & higher-order functions

```swift
let doubled = nums.map { $0 * 2 }
let evens   = nums.filter { $0 % 2 == 0 }
let total   = nums.reduce(0, +)
func load(completion: @escaping (Result<Data, Error>) -> Void) { ... }  // escaping
```
`map`/`filter`/`reduce` ≈ LINQ's `Select`/`Where`/`Aggregate`.

## 6. Error handling

```swift
enum ApiError: Error { case offline, badStatus(Int) }
func fetch() throws -> Data { throw ApiError.offline }
do { let d = try fetch() } catch ApiError.badStatus(let code) { print(code) } catch { print(error) }
let maybe = try? fetch()      // Data? (nil on throw)
```

## 7. async/await

```swift
func title(from url: URL) async throws -> String {
    let (data, _) = try await URLSession.shared.data(from: url)
    return String(decoding: data, as: UTF8.self)
}
Task { let t = try await title(from: url) }     // kick off async work
@MainActor func refreshUI() {}                   // hop to the main thread for UI
```

## 8. ARC & memory — the Objective-C inheritance

Classes are **reference-counted** (ARC), exactly as in Objective-C:
```swift
final class ViewModel {
    var onChange: (() -> Void)?
}
// Retain cycle risk: a closure capturing self strongly while self holds the closure.
vm.onChange = { [weak self] in self?.update() }    // [weak self] breaks the cycle
```
- Each strong reference increments the count; at 0 the object is deallocated (`deinit`).
- **Retain cycles** (two objects strongly referencing each other, or a closure capturing
  `self`) leak memory → use `weak`/`unowned` and capture lists `[weak self]`.
- `weak` is why **delegates** are usually declared `weak var delegate: ...` (Module 03).

## 9. Property wrappers (you'll see these everywhere in SwiftUI)

```swift
@propertyWrapper struct Clamped {
    var wrappedValue: Int { didSet { wrappedValue = min(max(wrappedValue, 0), 100) } }
}
```
SwiftUI's `@State`, `@Binding`, `@Observable` are property wrappers — Module 02.

---

## Do the lab
Practice value-vs-reference, optionals, enums, closures, and a retain cycle — runnable
from the command line. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
value vs reference type · optional · `protocol` + extension · associated values ·
closure · `@escaping` · `throws`/`try?` · `async`/`await` · ARC · retain cycle ·
`weak`/`unowned` · property wrapper

**Next →** [Module 02: SwiftUI Fundamentals](../02-swiftui-fundamentals/)

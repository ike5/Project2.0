# Swift Syntax Cheatsheet (for a C#/Java dev)

Fast reference mapping what you know to Swift. Swift 5 mode / Xcode 16.

## Variables & types
```swift
let name = "Ada"          // constant (prefer this)
var count = 0             // mutable
let pi: Double = 3.14159  // explicit type
let items = [1, 2, 3]     // [Int]
let map = ["a": 1]        // [String: Int]
let (x, y) = (1, 2)       // tuple destructuring
```
- Value types: `struct`, `enum`, tuples, most stdlib types (copied).
- Reference types: `class` (shared, ARC).

## Optionals (no nulls)
```swift
var maybe: String? = nil
if let value = maybe { print(value) }         // unwrap if present
guard let value = maybe else { return }       // early-exit unwrap
let len = maybe?.count ?? 0                    // optional chaining + default
let forced = maybe!                            // force-unwrap (crashes if nil — avoid)
```

## Functions & closures
```swift
func add(_ a: Int, _ b: Int) -> Int { a + b }     // _ = no argument label
func greet(name: String, loud: Bool = false) -> String { ... }   // default param
let double = { (n: Int) -> Int in n * 2 }          // closure
nums.map { $0 * 2 }                                 // trailing closure + $0 shorthand
func fetch(completion: @escaping (Data) -> Void) {} // escaping closure
```

## Structs, classes, enums
```swift
struct Point { var x: Int; var y: Int }            // value type, memberwise init
class Account {                                     // reference type
    let owner: String
    private(set) var balance = 0.0                  // read public, write private
    init(owner: String) { self.owner = owner }
    func deposit(_ a: Double) { balance += a }
}
enum Direction { case north, south, east, west }
enum Result2 { case success(String); case failure(Error) }   // associated values
```

## Protocols & extensions (protocol-oriented)
```swift
protocol Greeter { func greet() -> String }
extension Greeter { func greet() -> String { "hi" } }   // default implementation
struct Person: Greeter {}
extension String { var shout: String { uppercased() + "!" } }   // add to existing type
```

## Properties
```swift
struct Circle {
    var radius: Double
    var area: Double { .pi * radius * radius }      // computed property
    lazy var cached = expensive()                   // computed once on first access
    didSet { print("changed") }                     // property observer (on stored vars)
}
```

## Error handling
```swift
enum NetError: Error { case offline, badStatus(Int) }
func load() throws -> Data { throw NetError.offline }
do {
    let data = try load()
} catch NetError.badStatus(let code) {
    print(code)
} catch {
    print(error)            // 'error' is implicit
}
let maybe = try? load()     // -> Data?  (nil on throw)
```

## Generics
```swift
func firstOrNil<T>(_ xs: [T]) -> T? { xs.first }
struct Box<T> { var value: T }
func maxOf<T: Comparable>(_ a: T, _ b: T) -> T { a >= b ? a : b }   // constraint
```

## Concurrency (async/await)
```swift
func fetchTitle() async throws -> String {
    let (data, _) = try await URLSession.shared.data(from: url)
    return String(decoding: data, as: UTF8.self)
}
Task { let t = try await fetchTitle() }       // start async work
@MainActor func updateUI() { }                  // run on the main thread
```

## Memory (ARC) — the Obj-C inheritance
```swift
class Node { var next: Node? }
weak var delegate: SomeDelegate?               // non-owning -> avoids retain cycles
{ [weak self] in self?.doThing() }             // capture list in a closure
```
> Classes are reference-counted (ARC). Two objects strongly referencing each other =
> a **retain cycle** (leak); break it with `weak`/`unowned`.

## C# → Swift quick map
| C# | Swift |
|----|-------|
| `string?` | `String?` |
| `var`/`const` | `var`/`let` |
| `interface` | `protocol` |
| `class` (ref) | `class` |
| `struct` (val) | `struct` |
| `async`/`await` | `async`/`await` |
| `?.` / `??` | `?.` / `??` |
| `IEnumerable.Where/Select` | `filter`/`map` |
| `using`/`IDisposable` | `defer` / `deinit` |

// Reference solution for Challenge 01.  Run:  swift Solution.swift
import Foundation

// 1. Protocol + default + generic
protocol Summable {
    static func + (a: Self, b: Self) -> Self
    static var zero: Self { get }
}
extension Int: Summable { static var zero: Int { 0 } }
extension Double: Summable { static var zero: Double { 0 } }

func total<T: Summable>(_ xs: [T]) -> T {
    xs.reduce(T.zero, +)
}

// 2. Optional pipeline
func firstEven(_ xs: [Int]) -> Int? {
    xs.first(where: { $0 % 2 == 0 })
}

// 3. Result-style error handling
func parsePort(_ s: String) -> Result<Int, String> {
    guard let n = Int(s) else { return .failure("'\(s)' is not a number") }
    guard (1...65535).contains(n) else { return .failure("\(n) out of range") }
    return .success(n)
}

// 4. Retain cycle + fix
final class Ticker {
    var onTick: (() -> Void)?
    func fire() { onTick?() }
    deinit { print("deinit Ticker") }
}

// 5. Property wrapper
@propertyWrapper
struct Capitalized {
    private var value = ""
    var wrappedValue: String {
        get { value }
        set { value = newValue.isEmpty ? newValue : newValue.prefix(1).uppercased() + newValue.dropFirst() }
    }
    init(wrappedValue: String) { self.wrappedValue = wrappedValue }
}
struct User { @Capitalized var name: String }

// --- demo ---
print(total([1, 2, 3, 4]))          // 10
print(total([1.5, 2.5]))            // 4.0

print(firstEven([1, 3, 4]) ?? -1)   // 4
print(firstEven([1, 3, 5]) ?? -1)   // -1

switch parsePort("8080") { case .success(let p): print("port \(p)"); case .failure(let m): print(m) }
switch parsePort("99999") { case .success(let p): print("port \(p)"); case .failure(let m): print(m) }

// leak: closure captures self strongly while self stores the closure
do {
    let t = Ticker()
    t.onTick = { print("tick (leaking) \(t.onTick != nil)") }   // captures t strongly -> no deinit
}
print("— after leaking scope (no deinit above) —")
// fixed:
do {
    let t = Ticker()
    t.onTick = { [weak t] in print("tick ok \(t != nil)") }     // weak -> deinit fires
}
print("— after fixed scope (deinit Ticker should appear) —")

var u = User(name: "ada"); print(u.name)   // Ada

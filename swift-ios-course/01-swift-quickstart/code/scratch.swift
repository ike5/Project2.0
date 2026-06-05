// Run from the command line on a Mac:  swift scratch.swift
// A single-file Swift script exercising the language features from Module 01.
import Foundation

// 1. Value vs reference
struct PointS { var x = 0 }
final class PointC { var x = 0 }

var a = PointS(); let b0 = a; a.x = 9
let c = PointC(); let d0 = c; d0.x = 9
print("struct copy -> first stays:", PointS().x, "| b0.x:", b0.x)   // 0 | 0
print("class shares -> c.x:", c.x)                                   // 9

// 2. Optionals
func maybeName(_ present: Bool) -> String? { present ? "Ada" : nil }
let name = maybeName(false)
print("optional default:", name?.count ?? -1)                        // -1

// 3. Enum with associated values + switch
enum Loadable { case loading, loaded(String), failed(String) }
func describe(_ s: Loadable) -> String {
    switch s {
    case .loading: return "loading…"
    case .loaded(let v): return "loaded: \(v)"
    case .failed(let e): return "failed: \(e)"
    }
}
print(describe(.loaded("places")))

// 4. Closures / higher-order
let nums = [1, 2, 3, 4, 5]
print("doubled evens sum:", nums.filter { $0 % 2 == 0 }.map { $0 * 2 }.reduce(0, +))  // 12

// 5. Error handling
enum ApiError: Error { case offline }
func fetch(ok: Bool) throws -> String { if ok { return "data" } else { throw ApiError.offline } }
print("try? on failure:", (try? fetch(ok: false)) ?? "nil")          // nil

// 6. ARC retain cycle demo
final class Node {
    let name: String
    var friend: Node?                 // strong by default
    weak var weakFriend: Node?        // non-owning
    init(_ name: String) { self.name = name }
    deinit { print("deinit \(name)") }
}
do {
    let x = Node("X"); let y = Node("Y")
    x.weakFriend = y; y.weakFriend = x   // no cycle -> both deinit at scope end
}
print("end of demo")

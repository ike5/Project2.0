// Run on a Mac:  swift bridging_demo.swift
// Demonstrates the Swift <-> Objective-C bridge and the four classic Cocoa patterns.
import Foundation

print("== Value bridging ==")
let swiftStr = "Café au lait"
let ns: NSString = swiftStr as NSString
print("NSString.length (UTF-16):", ns.length)
print("NSString.substring(to: 4):", ns.substring(to: 4))     // "Café"
let back: String = ns as String
print("round-trips:", back == swiftStr)

let boxed: NSNumber = 42
print("NSNumber:", boxed.intValue, boxed.doubleValue, boxed.stringValue)

let nsArray: NSArray = [3, 1, 2] as NSArray
print("NSArray.count:", nsArray.count, "firstObject:", nsArray.firstObject ?? "nil")

print("\n== @objc + KVO ==")
final class Counter: NSObject {
    @objc dynamic var value: Int = 0       // @objc dynamic enables KVO
}
let counter = Counter()
let kvoToken = counter.observe(\.value, options: [.old, .new]) { _, change in
    print("KVO value: \(change.oldValue ?? 0) -> \(change.newValue ?? 0)")
}
counter.value = 5
counter.value = 9
kvoToken.invalidate()

print("\n== NotificationCenter (pub/sub) ==")
let noteName = Notification.Name("DidFinishThing")
let center = NotificationCenter.default
let obsToken = center.addObserver(forName: noteName, object: nil, queue: nil) { note in
    let who = note.userInfo?["who"] as? String ?? "?"
    print("observed notification from:", who)
}
center.post(name: noteName, object: nil, userInfo: ["who": "demo"])
center.removeObserver(obsToken)

print("\n== Selectors & target-action ==")
final class Button: NSObject {
    private var action: Selector?
    private weak var target: NSObject?       // delegates/targets are typically weak
    func addTarget(_ target: NSObject, action: Selector) {
        self.target = target; self.action = action
    }
    func tap() {
        if let action, let target, target.responds(to: action) {
            target.perform(action)            // send the message (Obj-C dynamism)
        }
    }
}
final class ViewController: NSObject {
    @objc func handleTap() { print("handleTap fired") }
}
let vc = ViewController()
let button = Button()
button.addTarget(vc, action: #selector(ViewController.handleTap))
button.tap()

// Reference solution for Challenge 03.  Run:  swift Solution.swift   (macOS)
import Foundation

// 1. KVO on two properties
final class Download: NSObject {
    @objc dynamic var progress: Double = 0
    @objc dynamic var isFinished: Bool = false
}
let dl = Download()
let t1 = dl.observe(\.progress, options: [.new]) { obj, change in
    let p = change.newValue ?? 0
    print(String(format: "progress: %.2f", p))
    if p >= 1.0 { obj.isFinished = true }
}
let t2 = dl.observe(\.isFinished, options: [.new]) { _, change in
    if change.newValue == true { print("download finished!") }
}
for step in stride(from: 0.25, through: 1.0, by: 0.25) { dl.progress = step }
t1.invalidate(); t2.invalidate()

// 2. NotificationCenter bus
extension Notification.Name { static let scoreChanged = Notification.Name("scoreChanged") }
let center = NotificationCenter.default
let a = center.addObserver(forName: .scoreChanged, object: nil, queue: nil) { n in
    print("A saw score:", n.userInfo?["score"] as? Int ?? -1)
}
let b = center.addObserver(forName: .scoreChanged, object: nil, queue: nil) { n in
    print("B saw score:", n.userInfo?["score"] as? Int ?? -1)
}
center.post(name: .scoreChanged, object: nil, userInfo: ["score": 10])
center.removeObserver(a); center.removeObserver(b)
center.post(name: .scoreChanged, object: nil, userInfo: ["score": 20])   // no output now
print("posted again after removal (silence above is correct)")

// 3. Closure-based TrafficLight
final class TrafficLight {
    var onChange: ((String) -> Void)?
    private let colors = ["red", "green", "yellow"]
    private var i = 0
    func advance() { i = (i + 1) % colors.count; onChange?(colors[i]) }
}
let light = TrafficLight()
light.onChange = { print("closure: now \($0)") }
light.advance(); light.advance()
// Delegate is preferable when there are MANY related callbacks (a protocol groups them)
// or the callee needs identity/lifetime. A closure is preferable for a single, local,
// inline reaction (less boilerplate).

// 4. Bridging quiz
// [String: Any] -> NSDictionary (automatic)
// Date -> NSDate (automatic);  URL -> NSURL (automatic);  Int -> NSNumber (automatic)
// JSON gotcha: NSJSONSerialization decodes numbers as NSNumber. `value as? Int` can fail
// if the bridge sees it as a different boxed numeric; prefer (value as? NSNumber)?.intValue,
// or better, decode with Codable into a typed model.
print("done")

# Lab 03 — Bridging & the Cocoa Patterns

**You'll:** see value bridging, KVO, NotificationCenter, and target-action run, then
build a **delegate**-based component yourself. ⏱️ ~50 min. Run on **macOS**.

---

## Part A — Run the demo
```bash
cd swift-ios-course/03-objc-heritage-bridging/code
swift bridging_demo.swift
```
✅ Expected (order matters):
```
== Value bridging ==
NSString.length (UTF-16): 12
NSString.substring(to: 4): Café
round-trips: true
NSNumber: 42 42.0 42
NSArray.count: 3 firstObject: 3

== @objc + KVO ==
KVO value: 0 -> 5
KVO value: 5 -> 9

== NotificationCenter (pub/sub) ==
observed notification from: demo

== Selectors & target-action ==
handleTap fired
```
Read [`bridging_demo.swift`](./code/bridging_demo.swift) and match each block to §2–§4 of
the README. Note `@objc dynamic` (KVO), `#selector`, and `weak` target.

## Part B — Experiment
- Remove `dynamic` from `Counter.value` and re-run — KVO stops reporting (the runtime
  hook is gone). Put it back.
- Change `responds(to:)` to observe a wrong selector and watch the guard prevent a crash.

## Part C — Build a delegate-based component
Create `traffic.swift`:
```swift
import Foundation

// The delegate contract (like CLLocationManagerDelegate, UITableViewDelegate, ...)
protocol TrafficLightDelegate: AnyObject {            // AnyObject -> class-only -> allows weak
    func light(_ light: TrafficLight, didChangeTo color: String)
}

final class TrafficLight {
    weak var delegate: TrafficLightDelegate?          // weak: avoid a retain cycle
    private let colors = ["red", "green", "yellow"]
    private var index = 0
    func advance() {
        index = (index + 1) % colors.count
        delegate?.light(self, didChangeTo: colors[index])   // call back the delegate
    }
}

final class Dashboard: TrafficLightDelegate {
    func light(_ light: TrafficLight, didChangeTo color: String) {
        print("dashboard: light is now \(color)")
    }
}

let light = TrafficLight()
let dash = Dashboard()
light.delegate = dash
light.advance(); light.advance(); light.advance()
```
```bash
swift traffic.swift
```
✅ Expected:
```
dashboard: light is now green
dashboard: light is now yellow
dashboard: light is now red
```
You just implemented the **delegate pattern** by hand — the exact shape of
`CLLocationManagerDelegate` (Module 07) and the **Coordinator** in SwiftoUI↔UIKit bridging
(Module 08).

## Part D — Why `weak`?
Make `delegate` a strong `var` and have `Dashboard` also hold the `TrafficLight` — add
`deinit` prints to both and wrap in a `do { }` scope. You'll see neither deallocates (a
retain cycle). Restore `weak` → both `deinit`. This is *why* Cocoa delegates are `weak`.

## What you learned
- Value bridging (`String`/`NSString`, `NSNumber`, `NSArray`) in practice.
- KVO (`@objc dynamic`), NotificationCenter, and target-action/selectors.
- The **delegate** pattern and why delegates are `weak`.

➡️ **[challenge.md](./challenge.md)** then [Module 04](../04-foundation-essentials-1/).

# Challenge 03 — Bridging in Depth

Solution in [`solutions/`](./solutions/). Try first. Runnable with `swift file.swift` on macOS.

## Tasks
1. **KVO observer.** Model a `Download: NSObject` with `@objc dynamic var progress: Double`
   and `@objc dynamic var isFinished: Bool`. Observe both; when `progress` reaches 1.0,
   set `isFinished = true`. Drive it from a loop and print transitions.

2. **NotificationCenter bus.** Build a tiny event bus: one object posts a custom
   `Notification.Name` with a typed payload in `userInfo`; two independent observers
   react. Remove the observers and show they stop receiving.

3. **Delegate vs closure (short answer + code).** Convert the Lab's `TrafficLight` to use
   a **closure** callback instead of a delegate. Then explain one situation where a
   delegate is preferable and one where a closure is.

4. **Bridging quiz (short answer).** For each, name the `NS*` type and whether the bridge
   is automatic: `[String: Any]`, `Date`, `URL`, `Int`. And: why might
   `someDictionary["count"] as? Int` fail if the value came from `NSJSONSerialization`?
   (Hint: `NSNumber`.)

## Success criteria
- [ ] KVO observes two properties and reacts to the threshold.
- [ ] A working notification bus with add/remove of observers.
- [ ] A closure-based `TrafficLight` plus a clear delegate-vs-closure trade-off.
- [ ] Correct bridging answers, including the `NSNumber` JSON gotcha.

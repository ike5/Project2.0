# Module 03 — Objective-C Heritage & Bridging

**Goal:** understand *why* the iOS frameworks look and feel the way they do, and master
the bridge between Swift and the Objective-C runtime they're built on. This is the
conceptual spine of the whole course. ⏱️ ~2.5 h · 🎯 Prereq: 00–02.

> Companion reference: [cheatsheets/foundation-bridging.md](../cheatsheets/foundation-bridging.md).

---

## 1. The heritage

UIKit, Foundation, Core Data, AVFoundation, Core Location, MapKit — almost all of the
"big" iOS frameworks were written in **Objective-C** (some predating iOS, going back to
NeXTSTEP — hence the `NS` prefix). Swift was designed to **interoperate** with them
seamlessly. So you write modern Swift, but you're constantly calling into 30-year-old
Objective-C designs. Recognizing those designs makes the APIs predictable.

Objective-C is a **dynamic, message-passing** language: `[object doThing:arg]` sends a
*message* resolved at runtime. That dynamism powers selectors, target-action, and KVO —
patterns you'll meet constantly.

## 2. Value bridging (automatic)

Swift auto-converts between native types and Foundation `NS*` types:

| Swift | Objective-C |
|-------|-------------|
| `String` ↔ `NSString` |
| `Int`/`Double`/`Bool` ↔ `NSNumber` |
| `Array`/`Dictionary`/`Set` ↔ `NSArray`/`NSDictionary`/`NSSet` |
| `Data` ↔ `NSData`, `Date` ↔ `NSDate`, `URL` ↔ `NSURL`, `Error` ↔ `NSError` |

```swift
let s = "Café"
let ns = s as NSString          // bridge up to use NSString APIs
print(ns.length)                // UTF-16 length
let boxed: NSNumber = 42        // Int boxes into NSNumber
```
You verified this in **FoundationKata** (`Bridging.swift`).

## 3. Exposing Swift to Objective-C: `@objc`

The Obj-C runtime only sees Swift you explicitly expose. You need `@objc` (often plus
inheriting from `NSObject`) for **selectors, target-action, KVO**, and some framework
callbacks.

```swift
class Handler: NSObject {
    @objc func handleTap() { print("tapped") }
}
```

## 4. The four patterns you'll see everywhere

### a) Delegates (the dominant callback style)
Instead of closures, a framework calls **methods on a delegate object** you assign:
```swift
final class LocationVM: NSObject, CLLocationManagerDelegate {
    let manager = CLLocationManager()
    override init() { super.init(); manager.delegate = self }
    func locationManager(_ m: CLLocationManager, didUpdateLocations locs: [CLLocation]) { /* ... */ }
}
```
Delegates are usually held **`weak`** (Module 01's retain-cycle lesson) — e.g.
`weak var delegate: ...`. You'll bridge delegate-based APIs into SwiftUI in Module 08
(the **Coordinator** is just a delegate).

### b) Target-action (classic UIKit events)
```swift
button.addTarget(self, action: #selector(tapped), for: .touchUpInside)
@objc func tapped() {}
```
A **selector** is a method name as a runtime value (`#selector(...)`). "On this event,
send this selector to that target."

### c) KVO (Key-Value Observing)
Be notified when a property changes — used by many frameworks (e.g. `AVPlayer` status):
```swift
class Model: NSObject { @objc dynamic var progress = 0.0 }
let token = model.observe(\.progress, options: [.new]) { _, change in print(change.newValue!) }
```
Requires `@objc dynamic`.

### d) NotificationCenter (broadcast pub/sub)
```swift
let token = NotificationCenter.default.addObserver(forName: .init("DidThing"), object: nil, queue: .main) { note in /* ... */ }
NotificationCenter.default.post(name: .init("DidThing"), object: nil, userInfo: ["k": "v"])
```
Foundation's app-wide event bus (keyboard show/hide, app lifecycle, etc.).

## 5. Mixed Swift/Objective-C projects (FYI)

If you add Objective-C files to a Swift app, Xcode offers to create a **bridging header**
(`<App>-Bridging-Header.h`) that `#import`s the Obj-C headers so Swift can see them.
Going the other way, Swift exposed with `@objc` appears in a generated
`<Module>-Swift.h`. You may need this when integrating Obj-C SDKs — and the **Unity**
plugin in Phase 2 is exactly this kind of mixed-language bridge.

## 6. Why this matters for SwiftUI & Unity

- SwiftUI sits *on top of* these frameworks; the moment you need location, media, Core
  Data, or a UIKit control, you're using Objective-C-era APIs through Swift.
- **Unity-as-a-Library** is a UIKit/Objective-C framework you drive from native code and
  call back into via the Obj-C runtime — the bridging skills here are exactly what make
  the capstone possible.

---

## Do the lab
Run a bridging demo (NSString/NSNumber/KVO/NotificationCenter/selectors) and build a
delegate-based component. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
Objective-C · `NS` prefix · message passing · value bridging · `@objc`/`@objcMembers` ·
`NSObject` · selector · `#selector` · target-action · delegate (`weak`) · KVO
(`@objc dynamic`) · NotificationCenter · bridging header · generated `-Swift.h`

**Next →** [Module 04: Foundation Essentials I](../04-foundation-essentials-1/)

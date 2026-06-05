# Foundation & Objective-C Bridging Cheatsheet

How Swift talks to the Objective-C-era frameworks. This is the conceptual core of the
course.

## The big idea

Most iOS frameworks (UIKit, Foundation, Core Data, …) were written in **Objective-C**.
Swift **bridges** to them: it auto-converts between native Swift types and their
Objective-C (`NS*`) counterparts so you can write idiomatic Swift against old APIs.

## Automatic value bridging (free conversions)

| Swift | Objective-C / Foundation |
|-------|--------------------------|
| `String` | `NSString` |
| `Int`, `Double`, `Bool` | `NSNumber` |
| `Array<T>` | `NSArray` |
| `Dictionary<K,V>` | `NSDictionary` |
| `Set<T>` | `NSSet` |
| `Data` | `NSData` |
| `Date` | `NSDate` |
| `URL` | `NSURL` |
| `Error` | `NSError` |

```swift
let s: String = "hello"
let ns: NSString = s as NSString        // explicit bridge up
let back: String = ns as String         // and back
let any: Any = 42
let n = any as? NSNumber                 // Int bridges to NSNumber
```
Often the bridge is automatic when an API expects the `NS` type.

## Toll-free bridging (Core Foundation ↔ Foundation)

Some C-level **Core Foundation** types (`CFString`, `CFArray`, …) are the *same memory*
as their Foundation counterparts (`NSString`, `NSArray`) — bridged "for free":
```swift
let cf: CFString = "hi" as CFString
let ns = cf as NSString                  // no copy
```
You'll meet this with lower-level APIs (Core Graphics, Security, etc.).

## Exposing Swift to Objective-C: `@objc`

The Obj-C runtime can only see Swift code you mark:
```swift
class Handler: NSObject {                 // must derive from NSObject for many cases
    @objc func handleTap() { }            // visible to selectors/target-action
}
@objcMembers class Model: NSObject {      // expose all members
    var title = ""
}
```
You need `@objc` for: **selectors**, **target-action**, **KVO**, `#selector(...)`, and
some framework delegate callbacks.

## Selectors & target-action (classic UIKit events)

```swift
button.addTarget(self, action: #selector(tapped), for: .touchUpInside)
@objc func tapped() { print("tapped") }

let timer = Timer.scheduledTimer(timeInterval: 1, target: self,
            selector: #selector(tick), userInfo: nil, repeats: true)
```
A **selector** is a method name as a runtime value. Target-action = "on this event,
send this selector to that target."

## Delegates (the dominant Cocoa callback pattern)

```swift
class LocationVM: NSObject, CLLocationManagerDelegate {
    let manager = CLLocationManager()
    override init() { super.init(); manager.delegate = self }
    func locationManager(_ m: CLLocationManager, didUpdateLocations locs: [CLLocation]) { }
}
```
Instead of closures, many Obj-C frameworks call **methods on a delegate** object you set.

## KVC / KVO

```swift
// KVC: get/set by string key (Obj-C dynamic)
let value = object.value(forKey: "title")

// KVO: observe a property's changes
let token = object.observe(\.progress, options: [.new]) { obj, change in
    print(change.newValue ?? 0)
}
```
KVO requires `@objc dynamic var` on the observed property.

## `NSNumber`, `NSError`, `NSNull`

```swift
let n = NSNumber(value: 3.14); let d = n.doubleValue
let err = NSError(domain: "MyApp", code: 42, userInfo: [NSLocalizedDescriptionKey: "boom"])
// JSON nulls bridge to NSNull (not nil) when using NSJSONSerialization
```

## When you'll feel the heritage
- Method names read like sentences: `tableView(_:didSelectRowAt:)`.
- Callbacks come via **delegates** and **target-action**, not just closures.
- Types are classes (`NSObject` subclasses) with reference semantics.
- Strings in APIs for keys (`Info.plist`, KVC, notification names).

Swift smooths most of this — but knowing the Obj-C model explains *why* the APIs look
the way they do, and is essential for bridging UIKit (and Unity) into SwiftUI.

# Glossary

Plain-English definitions of the terms in this course.

## Platform & tooling

- **Cocoa Touch** — Apple's iOS application frameworks (UIKit, Foundation, etc.), most
  of which originated in **Objective-C**. "Cocoa" is the macOS equivalent.
- **Xcode** — Apple's IDE for building iOS/macOS apps. Required; macOS-only.
- **iOS Simulator** — runs your app on a simulated iPhone/iPad on your Mac.
- **Swift Package Manager (SPM)** — Swift's built-in dependency/build tool;
  `Package.swift` describes a package. Text-based and `swift build`/`swift test`-able.
- **Target / Scheme** — a *target* produces one product (app, test bundle, framework);
  a *scheme* describes how to build/run a set of targets.
- **Info.plist** — an app's property-list config (bundle id, permissions usage strings,
  capabilities).
- **Bundle** — a structured folder treated as a single file (e.g. `MyApp.app`).

## Swift language

- **Optional** — a type that may hold a value or `nil` (`String?`); unwrap with
  `if let`, `guard let`, `??`, or `?.`.
- **Value type vs reference type** — `struct`/`enum` are **value types** (copied);
  `class` is a **reference type** (shared, ARC-managed).
- **Protocol** — a contract a type conforms to (like an interface); Swift favors
  **protocol-oriented** design + protocol extensions.
- **Closure** — an anonymous function/lambda; can capture surrounding variables.
- **ARC (Automatic Reference Counting)** — how Swift frees class instances: each strong
  reference adds 1; at 0 it's deallocated. **Inherited from Objective-C.**
- **`weak` / `unowned`** — non-owning references to break **retain cycles**.
- **Property wrapper** — a reusable attribute that adds behavior to a property
  (`@State`, `@Published`); the `@`-things in SwiftUI are property wrappers.
- **`@escaping`** — marks a closure that outlives the function call (e.g. stored or async).
- **`@MainActor` / `Sendable`** — Swift concurrency: run on the main thread / safe to
  pass across threads.

## Objective-C heritage & bridging

- **Objective-C** — the older language these frameworks were written in; dynamic,
  message-passing, `[obj method:arg]` syntax.
- **`NSObject`** — the root base class of Obj-C/Cocoa types.
- **`NS` prefix** — Foundation types from the NeXTSTEP/Obj-C era (`NSString`,
  `NSDate`, `NSArray`, `NSError`).
- **Bridging** — Swift automatically converts between Swift and Foundation types
  (`String↔NSString`, `Array↔NSArray`, `Dictionary↔NSDictionary`, `Int↔NSNumber`).
- **Toll-free bridging** — some Core Foundation (C) and Foundation (Obj-C) types are
  interchangeable for free (e.g. `CFString`/`NSString`).
- **`@objc` / `@objcMembers`** — expose Swift code to the Objective-C runtime (needed
  for selectors, target-action, KVO, some framework callbacks).
- **Bridging header** — a header that exposes Objective-C code to Swift in a mixed project.
- **Selector** — a method name as a runtime value (`#selector(handleTap)`); used by
  target-action and timers.
- **Target-action** — the classic UIKit event pattern: "on this control event, call
  this *action* on that *target*."
- **Delegate** — an object that another object calls back to (e.g.
  `UITableViewDelegate`, `CLLocationManagerDelegate`). The dominant Cocoa callback pattern.
- **KVC / KVO** — Key-Value Coding (access properties by string name) / Key-Value
  Observing (be notified when a property changes). Obj-C runtime features.

## Foundation

- **`Codable`** — Swift protocol for encoding/decoding to JSON/plist
  (`Encodable`+`Decodable`); modern replacement for `NSJSONSerialization`.
- **`URLSession`** — the networking API (downloads/uploads; `async/await` supported).
- **`UserDefaults`** — small key/value persistent store (settings).
- **`NotificationCenter`** — in-process publish/subscribe broadcast.
- **`FileManager`** — filesystem access (paths, directories, files).
- **`DateFormatter` / `Calendar`** — format/parse dates; calendar math.

## SwiftUI

- **`View`** — a protocol; a SwiftUI view is a value type with a `body`.
- **`some View`** — an opaque return type ("a specific View I won't name").
- **`@State` / `@Binding`** — local mutable state / a two-way reference to state owned
  elsewhere.
- **`@Observable` / `@StateObject` / `@ObservedObject`** — reference-type view models
  whose changes refresh the UI.
- **`@Environment`** — read values injected into the view hierarchy.
- **Modifier** — a method that returns a modified view (`.padding()`, `.foregroundStyle`).
- **`NavigationStack` / `List`** — navigation container / scrollable rows.

## Core Data

- **Core Data** — Apple's Obj-C-era object graph & persistence framework (an ORM-ish layer).
- **`NSManagedObject`** — an entity instance (a row).
- **`NSManagedObjectContext`** — the in-memory "scratchpad" you read/write through.
- **`NSPersistentContainer`** — sets up the stack (model + store + context).
- **`@FetchRequest`** — a SwiftUI property wrapper that live-queries Core Data.
- **SwiftData** — the modern, Swift-native successor (`@Model`, `@Query`).

## Media & location

- **AVFoundation** — audio/video framework (`AVAudioPlayer`, `AVPlayer`, capture).
- **Core Location** — GPS/location (`CLLocationManager`, authorization, updates).
- **MapKit** — maps; SwiftUI exposes a `Map` view.
- **PhotosUI** — the photo picker (`PhotosPicker`).

## UIKit interop & Unity

- **UIKit** — the original (Obj-C) iOS UI framework; SwiftUI can host UIKit and vice versa.
- **`UIViewRepresentable` / `UIViewControllerRepresentable`** — wrap a UIKit view/
  controller so SwiftUI can display it.
- **Coordinator** — a helper object (often the delegate) connecting a represented UIKit
  object back to SwiftUI.
- **Unity as a Library (UaaL)** — embedding the Unity runtime as a framework inside a
  native app rather than shipping a Unity-only app.
- **`UnityFramework`** — the compiled Unity runtime exposed as an iOS framework you
  control from native code (`getInstance()`, `runEmbedded`, `unloadApplication`).
- **`sendMessageToGOWithName:functionName:message:`** — call a method on a Unity
  GameObject from native code.
- **`NativeCallsProtocol` / `[DllImport("__Internal")]`** — the channel for Unity (C#)
  to call back into native (Swift/Obj-C) code.

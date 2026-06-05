# Swift for iOS: Objective-C-Era Frameworks, SwiftUI & Embedding Unity 🍎🎮

A hands-on, Mac-first course for a developer who **knows some Swift** and wants to master
the **Objective-C-derived Apple frameworks** (the "Cocoa Touch" libraries that power
real iOS apps), use them from **SwiftUI** in **Xcode**, and ultimately **embed a Unity
scene inside a SwiftUI app** (Unity as a Library).

> **Who this is for:** You can read basic Swift and have built apps before (this is the
> 4th course in the series, after the .NET/C# + Unity course). You want the *frameworks*
> — Foundation, Core Data, AVFoundation, Core Location, MapKit, UIKit interop — plus a
> real understanding of the **Objective-C heritage** beneath them, and a path to
> **Unity-in-iOS**.

---

## The arc

```
 Swift quick-start ─▶ SwiftUI foundation ─▶ Objective-C heritage & bridging
        │                                            │
        ▼                                            ▼
   the Obj-C-derived frameworks (Foundation, Core Data, media/location, UIKit interop)
        │
        ▼
   Embed Unity in a SwiftUI app  ◀── (ties back to your earlier Unity work)
```

Most of UIKit/Foundation/Core Data **originated in Objective-C**; Swift *bridges* to
them. Understanding that bridge is the theme of this course — and it's exactly what
makes embedding a UIKit-based engine like **Unity** possible.

---

## What makes it effective

- **Learn by doing.** Every module = concepts + a guided Xcode/Swift lab (with expected
  behavior) + an unguided challenge + reference solutions.
- **Obj-C heritage, made explicit.** You'll see *why* these APIs feel different
  (`NS*` types, delegates, target-action, KVO) and how Swift bridges to them.
- **One buildable kata.** `FoundationKata` is a real Swift Package you compile with
  `swift build`/`swift test` — the closest thing to instant feedback in iOS dev.
- **A through-line app.** `PlacesApp` grows across modules: notes → networking →
  Core Data → maps/media → a UIKit bridge → a Unity view.
- **Unity as a Library capstone.** Export a Unity iOS build, embed `UnityFramework`,
  and pass messages between Swift and Unity.

---

## Prerequisites

- A **Mac** with **Xcode 16+** (free from the Mac App Store) and ~30 GB free.
- Basic Swift familiarity (variables, functions, `struct`/`class`, `if let`).
- For the Unity phase: **Unity 6 LTS** + Unity Hub (from the earlier course), with
  **iOS Build Support** installed.

Versions used: **Xcode 16 / iOS 18 / Swift 5 language mode**, **Unity 6 LTS**.

---

## The learning path

### Phase 0 — Swift & SwiftUI foundation
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 00 | [Setup & Orientation](./00-setup/) | Install Xcode, run the Simulator, understand the Cocoa landscape | 45 min |
| 01 | [Swift Quick-Start](./01-swift-quickstart/) | Optionals, value vs reference, protocols, closures, ARC | 1.5 h |
| 02 | [SwiftUI Fundamentals](./02-swiftui-fundamentals/) | Views, state, layout, navigation | 2.5 h |

### Phase 1 — Objective-C heritage & frameworks
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 03 | [Objective-C Heritage & Bridging](./03-objc-heritage-bridging/) | `@objc`, bridging, delegates, target-action, KVO | 2.5 h |
| 04 | [Foundation Essentials I](./04-foundation-essentials-1/) | Strings, Date, Data, NSNumber, Error | 2 h |
| 05 | [Foundation Essentials II](./05-foundation-essentials-2/) | Codable/JSON, URLSession, UserDefaults, NotificationCenter | 2.5 h |
| 06 | [Core Data & SwiftData](./06-core-data/) | Persist data with the classic Obj-C ORM | 3 h |
| 07 | [Media & Location](./07-media-and-location/) | AVFoundation, Core Location, MapKit, Photos | 3 h |
| 08 | [UIKit ↔ SwiftUI Interop](./08-uikit-swiftui-interop/) | Bridge UIKit views/controllers into SwiftUI | 2.5 h |

### Phase 2 — Unity as a Library in iOS
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 09 | [Embedding Unity (UaaL)](./09-embedding-unity-uaal/) | Export & embed `UnityFramework` in a SwiftUI app | 3 h |
| 10 | [Swift ↔ Unity & Capstone](./10-unity-capstone/) | Two-way Swift↔Unity messaging; ship the app | 3+ h |

**Total: a realistic ~30 hours of focused, hands-on work.**

---

## How each module is structured

```
NN-topic/
├── README.md      ← Concepts + Obj-C heritage call-outs. Read first.
├── lab.md         ← Step-by-step Xcode/Swift lab with expected behavior. Do second.
├── code/          ← Reference .swift files the lab uses.
├── challenge.md   ← An unguided task. Do third.
└── solutions/     ← Reference answers — peek only after trying.
```

---

## Reference material (keep open)

- **[cheatsheets/swift-syntax.md](./cheatsheets/swift-syntax.md)** — Swift for a C#/Java dev
- **[cheatsheets/foundation-bridging.md](./cheatsheets/foundation-bridging.md)** — NSString↔String & toll-free bridging
- **[cheatsheets/swiftui.md](./cheatsheets/swiftui.md)** — views, state wrappers, modifiers, navigation
- **[cheatsheets/xcode-and-spm.md](./cheatsheets/xcode-and-spm.md)** — Xcode, Simulator, SPM, Info.plist, permissions
- **[GLOSSARY.md](./GLOSSARY.md)** — every term in plain English
- **[VERIFY.md](./VERIFY.md)** — end-to-end smoke test

## Shared projects

- **[apps/FoundationKata/](./apps/FoundationKata/)** — a buildable Swift Package (Foundation/bridging katas).
- **[apps/PlacesApp/](./apps/PlacesApp/)** — the SwiftUI through-line app.
- **[unity-ios/](./unity-ios/)** — the Unity-as-a-Library bridge code + integration guide.

---

## Quick start

```bash
cd swift-ios-course/00-setup
cat README.md            # install Xcode, run the Simulator
# verify the buildable kata:
cd ../apps/FoundationKata && swift test
cd ../../01-swift-quickstart && cat README.md
```

Ready? **→ [Start with Module 00: Setup & Orientation](./00-setup/)**

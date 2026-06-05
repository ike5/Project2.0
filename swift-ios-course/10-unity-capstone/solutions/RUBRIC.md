# Capstone — Self-Assessment Rubric

Score yourself honestly. Aim for "Solid" or better on each row.

| Capability | Needs work | Solid | Mastery |
|------------|-----------|-------|---------|
| **Swift fluency** | copies snippets | idiomatic Swift (optionals, value types, protocols) | reasons about ARC/retain cycles; explains Swift↔Obj-C |
| **SwiftUI** | renders a screen | state-driven views, navigation, lists | clean `@Observable` models, previews, modifiers |
| **Obj-C bridging** | unaware | uses `@objc`, delegates, KVO, NotificationCenter | explains the heritage and *why* APIs look as they do |
| **Foundation** | basic | Codable/URLSession/UserDefaults/FileManager | robust networking, caching, error handling |
| **Persistence** | none | SwiftData or Core Data CRUD | migrations/relationships; picks the right tool |
| **Device frameworks** | none | location/map/media with permissions | handles all auth states; delegate-based managers |
| **UIKit interop** | unaware | `UIViewControllerRepresentable` + Coordinator | two-way bridges; `UIHostingController` |
| **Unity embedding** | can't load it | launches & shows Unity from SwiftUI | lifecycle (pause/unload), memory-aware |
| **Swift↔Unity comms** | one-way | `sendMessage` in + callbacks out | typed/JSON messages, command enum, robust UX |

**You've reached the goal when** you can: build a SwiftUI app using the Objective-C-era
frameworks fluently, explain the bridge beneath them, and **embed a Unity scene that talks
to SwiftUI both ways**.

### Where this leads
- **Polish the app:** App Store signing, app icons, accessibility, localization.
- **Deeper interop:** custom Obj-C/C++ SDKs, Swift/C++ interop, `@_cdecl` exports.
- **Deeper Unity UaaL:** multiple scenes, AR (ARKit + Unity), shared rendering, passing
  textures/data efficiently, and packaging Unity content for updates.
- **Concurrency:** adopt Swift 6 strict concurrency (`@MainActor`, `Sendable`) across the
  app and the Unity bridge.

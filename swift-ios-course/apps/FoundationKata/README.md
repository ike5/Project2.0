# FoundationKata

A pure-Swift/Foundation **Swift Package** — the one piece of this course you can compile
and test instantly from the command line (no Xcode UI needed). It demonstrates the
Objective-C-derived **Foundation** APIs and **bridging** that Modules 03–05 cover.

## Run it
```bash
cd swift-ios-course/apps/FoundationKata
swift build
swift test
```
✅ Expected: `Build complete!` and all tests passing.

Because it uses only cross-platform Foundation, it also builds on Linux — handy for fast
iteration on the language/Foundation parts before moving into Xcode/SwiftUI.

## What's inside
| File | Shows |
|------|-------|
| `Sources/.../Bridging.swift` | `String↔NSString`, `Double↔NSNumber` bridging |
| `Sources/.../Dates.swift` | ISO-8601 formatting/parsing, calendar day math |
| `Sources/.../JSON.swift` | `Codable` encode/decode (the `Place` model) |
| `Sources/.../TextStats.swift` | small standard-library text utilities |
| `Tests/...` | XCTest coverage for all of the above |

Use this as a scratchpad: add a function, write a test, `swift test`, repeat.

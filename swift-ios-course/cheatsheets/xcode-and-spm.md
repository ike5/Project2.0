# Xcode, Simulator & Swift Package Manager Cheatsheet

## Xcode essentials

| Action | Shortcut |
|--------|----------|
| Build | `Cmd+B` |
| Run (build + launch) | `Cmd+R` |
| Stop | `Cmd+.` |
| Run tests | `Cmd+U` |
| Clean build folder | `Shift+Cmd+K` |
| Open quickly (file/symbol) | `Shift+Cmd+O` |
| Show/hide canvas (SwiftUI preview) | `Option+Cmd+Return` |
| Jump to definition | `Ctrl+Cmd+J` (or Cmd-click) |
| Rename symbol | `Ctrl+Cmd+E` (Editor ▸ Refactor ▸ Rename) |
| Show navigator / inspector | `Cmd+0` / `Option+Cmd+0` |

- **Canvas / Previews** — `#Preview { ... }` renders live; your fastest feedback loop.
- **Issue navigator** (`Cmd+5`) — build errors/warnings.
- **Debug area / console** — `print(...)` output and the lldb debugger.
- **Breakpoints** — click the gutter; `po expression` in the console to inspect.

## The Simulator
- Run picks a destination (e.g. *iPhone 16*). Change it in the scheme/destination menu.
- Hardware menu: Home, rotate, shake; **Features ▸ Location** to simulate GPS;
  **Device ▸ Erase All Content and Settings** to reset.
- `Cmd+Shift+H` = Home, `Cmd+K` = toggle software keyboard, `Cmd+→/←` = rotate.

## Project anatomy
- **`.xcodeproj` / `.xcworkspace`** — the project / a workspace grouping projects+packages.
- **Target** — produces one product (app, tests, framework). Has **Build Settings**,
  **Build Phases**, and an **Info.plist**/Info tab.
- **Scheme** — how to build/run/test/profile a target.
- **Asset catalog** (`Assets.xcassets`) — images, colors, the app icon.

## Info.plist & permissions (you'll need these a lot)
Add **usage description** keys or iOS denies the permission and may crash:
```
NSLocationWhenInUseUsageDescription   = "We use your location to show nearby places."
NSCameraUsageDescription              = "To take photos for your notes."
NSMicrophoneUsageDescription          = "To record voice memos."
NSPhotoLibraryUsageDescription        = "To attach photos."
```
In modern Xcode these live under the target's **Info** tab (or a custom `Info.plist`).

## Swift Package Manager (SPM)
Create a package:
```bash
mkdir MyKit && cd MyKit
swift package init --type library      # or --type executable
swift build
swift test
swift run                              # for executables
```
`Package.swift` (the manifest):
```swift
// swift-tools-version: 5.9
import PackageDescription
let package = Package(
    name: "MyKit",
    products: [.library(name: "MyKit", targets: ["MyKit"])],
    targets: [
        .target(name: "MyKit"),
        .testTarget(name: "MyKitTests", dependencies: ["MyKit"]),
    ]
)
```
Add a dependency:
```swift
dependencies: [ .package(url: "https://github.com/apple/swift-algorithms", from: "1.2.0") ],
// then in a target:
.target(name: "MyKit", dependencies: [.product(name: "Algorithms", package: "swift-algorithms")])
```
In Xcode: **File ▸ Add Package Dependencies…** to add SPM packages to an app.

## Signing & running on a device (brief)
- Free Apple ID works for development. Target ▸ **Signing & Capabilities** ▸ select your
  **Team** ▸ let Xcode manage signing. Connect an iPhone, trust the computer, pick it as
  the run destination. (The Simulator needs no signing.)

## XcodeGen (optional, used by PlacesApp)
A text `project.yml` generates the `.xcodeproj` so projects are diff-friendly:
```bash
brew install xcodegen
xcodegen generate        # reads project.yml -> creates PlacesApp.xcodeproj
open PlacesApp.xcodeproj
```

# End-to-End Verification

Run this after **Module 00** to confirm your toolchain works, and any time something
feels off. Most of this requires **macOS + Xcode**.

## 0. Xcode & toolchain
```bash
xcode-select -p                 # prints the active Xcode path
xcodebuild -version             # Xcode 16.x
swift --version                 # Swift 5.x / 6 toolchain bundled with Xcode
```
✅ Versions print. If `xcode-select` errors, install Xcode from the App Store and run
`xcode-select --install` for the command-line tools.

## 1. The buildable kata compiles & tests
```bash
cd swift-ios-course/apps/FoundationKata
swift build
swift test
```
✅ Expected: `Build complete!` then a passing test run
(`Test Suite 'All tests' passed`). This package uses only cross-platform Foundation, so
it also builds on Linux — it's your fast feedback loop for the language/Foundation parts.

## 2. Create & run a SwiftUI app (Simulator)
1. Xcode ▸ **File ▸ New ▸ Project… ▸ iOS ▸ App**. Name `HelloiOS`, Interface **SwiftUI**,
   Language **Swift**. Save anywhere.
2. Pick an **iPhone 16** simulator in the destination menu.
3. Press **Run** (`Cmd+R`).

✅ Expected: the Simulator boots and shows "Hello, world!". Edit the `Text` in
`ContentView.swift` and the preview/canvas updates.

## 3. PlacesApp (the through-line app)
After Module 02 you'll have `PlacesApp` runnable. Two ways to open it:
- **XcodeGen (reproducible):**
  ```bash
  brew install xcodegen
  cd swift-ios-course/apps/PlacesApp
  xcodegen generate
  open PlacesApp.xcodeproj
  ```
- **Manual:** create an App project and add the `.swift` files from `apps/PlacesApp/Sources/`
  (each module's `lab.md` lists exactly which).

✅ Build & run → the app launches in the Simulator. Each module's lab states the expected
on-screen behavior (a list, a detail screen, a map, etc.).

## 4. Permissions sanity (Module 07)
When you add location/camera/photos, confirm the **Info** usage strings exist; on first
use the Simulator shows the system permission prompt. Simulate GPS via
**Simulator ▸ Features ▸ Location**.

## 5. (Phase 2) Unity as a Library
After Modules 09–10 you'll also verify:
```text
- Unity 6 (with iOS Build Support) exports an Xcode project containing UnityFramework.
- The SwiftUI app embeds UnityFramework and launches a Unity view.
- A button in SwiftUI changes something in Unity (native → Unity), and Unity reports a
  value back into SwiftUI (Unity → native).
```

---

🎉 **Steps 0–2 green?** Your environment is ready. Begin with
[Module 01](./01-swift-quickstart/) (or [Module 00](./00-setup/) for setup).

Trouble? See [cheatsheets/xcode-and-spm.md](./cheatsheets/xcode-and-spm.md) and the
Troubleshooting section in [00-setup/README.md](./00-setup/README.md).

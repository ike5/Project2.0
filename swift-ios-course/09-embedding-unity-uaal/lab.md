# Lab 09 — Embed & Launch Unity

**You'll:** produce `UnityFramework.framework`, embed it in a SwiftUI app, and launch a
Unity scene from a button. ⏱️ ~90 min. **Build on a Mac with Unity 6 (iOS Build Support)
+ Xcode.**

> Keep Unity's official **`uaal-example`** open for your exact version — menu paths and a
> couple of integration details vary. The steps below are the stable shape.

---

## Part A — A minimal Unity scene
1. Open Unity 6, create/open a small project. In a scene, add a **Cube** and a **Light**
   so there's something visible. Save the scene and add it to **Build Settings ▸ Scenes
   In Build**.
2. **File ▸ Build Settings ▸ iOS ▸ Switch Platform**.
3. **Player Settings:** set a Bundle Identifier (e.g. `com.example.unitycontent`).
4. **Build** → output to a folder like `~/dev/UnityBuild`. Unity generates an Xcode
   project with **`Unity-iPhone`** and **`UnityFramework`** targets.

✅ You now have a Unity-generated Xcode project containing `UnityFramework`.

## Part B — Get UnityFramework.framework
Open the generated Xcode project, select the **UnityFramework** scheme, and **Build** it
(for your run destination). The product is `UnityFramework.framework`.

> Many teams instead add the Unity-generated project into the **same workspace** as the
> app and depend on the `UnityFramework` target directly — that avoids copying. Either
> approach works; the `uaal-example` documents both.

## Part C — Embed it in a SwiftUI app
1. Create (or reuse) a SwiftUI app project.
2. Target ▸ **General ▸ Frameworks, Libraries, and Embedded Content** → **+** →
   add `UnityFramework.framework` → set **Embed & Sign**.
3. Add Unity's **`Data`** folder to the app bundle (drag it in; "Create folder
   references") so `setDataBundleId` can find it (see `uaal-example` for the exact data
   layout for your Unity version).
4. Add the native glue from [`unity-ios/ios/`](../unity-ios/ios/):
   - `UnityBridge.swift`
   - `NativeCallsPlugin.mm` (Xcode will offer to create a bridging header — accept it, or
     add `App-Bridging-Header.h` and set **Build Settings ▸ Objective-C Bridging Header**).
5. Add `setExecuteHeader` shim: create a tiny Obj-C function that calls
   `[ufw setExecuteHeader:&_mh_execute_header];` and call it from `UnityBridge` after
   `getInstance()` (copy this from `uaal-example`; pure Swift can't reach the header).

## Part D — Launch from SwiftUI
Add `UnityContainerView.swift` from `unity-ios/ios/`. Then a launcher:
```swift
struct ContentView: View {
    @State private var showUnity = false
    var body: some View {
        VStack(spacing: 20) {
            Text("Native SwiftUI screen").font(.title2)
            Button("Launch Unity") { showUnity = true }
        }
        .fullScreenCover(isPresented: $showUnity) {
            ZStack(alignment: .topTrailing) {
                UnityContainerView().ignoresSafeArea()
                Button("Close") {
                    UnityBridge.shared.unload()
                    showUnity = false
                }
                .padding()
                .buttonStyle(.borderedProminent)
            }
        }
    }
}
```

## Part E — Run on a device
1. Select a real iPhone as the destination (UaaL is most reliable on device).
2. Set your signing **Team** (target ▸ Signing & Capabilities).
3. **Run**. Tap **Launch Unity**. ✅ Expected: your SwiftUI screen, then a full-screen
   Unity view showing the cube. Tap **Close** → `unloadApplication()` tears Unity down and
   you're back in SwiftUI.

## Troubleshooting (common UaaL issues)
- **Linker/symbol errors** → ensure `UnityFramework.framework` is **Embed & Sign**, and
  the Unity `Data` is in the bundle.
- **Crash on launch / black screen** → the `setExecuteHeader` shim is missing or
  `setDataBundleId` doesn't match where `Data` is.
- **"Unity already loaded"** → you tried to `runEmbedded` twice; use `showUnityWindow()`
  after the first load (the bridge handles this).
- **Won't relaunch after unload** → after `unloadApplication`, fully recreate via `show()`
  (the bridge resets `isLoaded` in `unityDidUnload`).

## What you learned
- Build a Unity iOS framework (`UnityFramework.framework`) and **embed** it.
- Drive the runtime via `UnityBridge` (`show`/`pause`/`unload`).
- Host Unity's view in SwiftUI with a `UIViewControllerRepresentable`.

➡️ **[challenge.md](./challenge.md)** then [Module 10](../10-unity-capstone/).

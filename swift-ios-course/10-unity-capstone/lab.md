# Lab 10 — Two-Way Bridge & Capstone

**You'll:** wire SwiftUI → Unity and Unity → SwiftUI, then assemble the capstone control
panel. ⏱️ ~100 min. Continue from your Module 09 embed.

---

## Part A — Unity side
1. In your Unity project, add [`NativeAPI.cs`](../unity-ios/unity/NativeAPI.cs) and
   [`SceneBridge.cs`](../unity-ios/unity/SceneBridge.cs) to `Assets/Scripts/`.
2. In the scene, create an empty GameObject named **exactly `SceneBridge`** and attach the
   `SceneBridge` component.
3. Assign its **Target Renderer** to the cube's Renderer; optionally assign a **Spawn
   Prefab** (any small prefab).
4. **Rebuild** the iOS framework (Module 09, Part A/B) so the new scripts are included.

## Part B — Native plugin
1. Ensure [`NativeCallsPlugin.mm`](../unity-ios/ios/NativeCallsPlugin.mm) is in the **app**
   target and the bridging header [`App-Bridging-Header.h`](../unity-ios/ios/App-Bridging-Header.h)
   is set (Build Settings ▸ *Objective-C Bridging Header*).
2. Add [`UnityContainerView.swift`](../unity-ios/ios/UnityContainerView.swift) if you
   haven't — it contains `UnityContainerView` and the `UnityEvents` observer.

## Part C — SwiftUI → Unity (commands in)
Add a temporary test button to your launcher:
```swift
Button("Make cube green") {
    UnityBridge.shared.send(toObject: "SceneBridge", method: "SetColor", message: "0,1,0")
}
```
Run on device, launch Unity, tap it. ✅ The cube turns **green** — SwiftUI invoked
`SceneBridge.SetColor("0,1,0")` via `sendMessage`.

> If nothing happens: the GameObject name must be exactly `SceneBridge`, the method
> `public` with one `string` param, and the framework rebuilt with the script included.

## Part D — Unity → SwiftUI (callbacks out)
`SceneBridge.Spawn` calls `NativeAPI.SendScore(score)`, and `Start()` calls
`NativeAPI.SendMessage("Unity scene ready")`. Observe them:
```swift
@State private var events = UnityEvents()
// in body:
Text("Score: \(events.score)")
Text(events.lastMessage)
Button("Spawn") { UnityBridge.shared.send(toObject: "SceneBridge", method: "Spawn", message: "") }
```
Run → on launch you should see **"Unity scene ready"**; each **Spawn** tap increments the
**Score** shown in SwiftUI. ✅ Unity → native → SwiftUI round-trip works.

## Part E — Assemble the capstone
Add [`code/CapstoneUnityView.swift`](./code/CapstoneUnityView.swift) and present it
(e.g. from your launcher's `fullScreenCover`). It gives you:
- a **ColorPicker** that live-updates the Unity cube (`SetColor`),
- a **Spawn** button (and a score badge that reflects Unity's callbacks),
- the latest **status message** from Unity,
- an **Unload Unity** button.

Run on device. ✅ Expected: change the color picker → cube recolors in real time; tap
Spawn → objects appear in Unity *and* the SwiftUI score climbs; tap Unload → Unity tears
down and you return to native UI.

🎉 **That's the capstone:** a SwiftUI app embedding and bidirectionally communicating with
Unity.

## Part F — Self-assess
Run through the [mastery rubric](./solutions/RUBRIC.md).

## What you learned
- SwiftUI → Unity via `sendMessageToGOWithName`.
- Unity → SwiftUI via `[DllImport("__Internal")]` + an Obj-C++ plugin + a callback bridge.
- Republishing native callbacks as `@Observable` SwiftUI state.
- A complete, bidirectional SwiftUI ⟷ Unity application.

➡️ **[challenge.md](./challenge.md)** and the [rubric](./solutions/RUBRIC.md).

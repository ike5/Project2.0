# Challenge 09 — Reference Notes

### 1. Pause on background
```swift
.onReceive(NotificationCenter.default.publisher(for: UIApplication.didEnterBackgroundNotification)) { _ in
    UnityBridge.shared.pause(true)
}
.onReceive(NotificationCenter.default.publisher(for: UIApplication.willEnterForegroundNotification)) { _ in
    UnityBridge.shared.pause(false)
}
```
> Pausing stops Unity's player loop, dropping CPU/GPU/battery use while backgrounded.

### 2. Embedded (sub-region)
```swift
VStack {
    Text("Above Unity").font(.headline)
    UnityContainerView()
        .frame(height: 300)
        .clipShape(RoundedRectangle(cornerRadius: 12))
    Button("Send command") { /* Module 10 */ }
}
```
> Because Unity's `rootView` is added with constraints to the hosted container VC, it
> fills whatever frame SwiftUI gives the representable.

### 3. Clean teardown
- `unloadApplication()` posts the unload notification → `UnityBridge.unityDidUnload` sets
  `ufw = nil` and `isLoaded = false`.
- Re-calling `show()` reloads the framework and `runEmbedded` again.
- **State to reset:** the cached `UnityFramework` instance, `isLoaded`, and the framework
  listener registration. Re-registration happens in `show()`.

### 4. Unload vs pause
> Unity holds significant **memory** (textures, meshes, the runtime). If the user has left
> the Unity screen, `unloadApplication()` frees most of that — important on memory-limited
> devices and to avoid jetsam termination. The trade-off: **reloading is slow** (re-init,
> re-load assets), so for a screen the user toggles frequently, `pause(true)` keeps Unity
> resident for instant resume at the cost of memory. Choose based on how often the user
> returns and how memory-hungry the scene is.

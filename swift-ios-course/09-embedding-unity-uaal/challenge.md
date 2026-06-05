# Challenge 09 — Lifecycle & Hosting

Notes in [`solutions/`](./solutions/). Most of this is integration work on your Mac.

## Tasks
1. **Pause on background.** Observe `UIApplication.didEnterBackgroundNotification` /
   `willEnterForegroundNotification` and call `UnityBridge.shared.pause(true/false)` so
   Unity stops rendering when the app is backgrounded. Verify CPU drops when backgrounded.

2. **Embedded, not full-screen.** Instead of `fullScreenCover`, embed
   `UnityContainerView()` in a fixed-height frame inside a SwiftUI screen with native
   controls above and below it. Confirm Unity renders in just that region.

3. **Clean teardown.** After `unload()`, relaunch Unity and confirm it works a second
   time (the bridge resets state in `unityDidUnload`). Note in writing what state must be
   reset between loads.

4. **Memory awareness (short answer).** Why is it important to `unloadApplication()` when
   leaving the Unity screen, and what are the trade-offs of unloading vs just pausing?

## Success criteria
- [ ] Unity pauses/resumes with app background/foreground.
- [ ] Unity renders embedded in a sub-region with native UI around it.
- [ ] Unity can be unloaded and relaunched cleanly.
- [ ] Clear reasoning on unload vs pause (memory vs reload cost).

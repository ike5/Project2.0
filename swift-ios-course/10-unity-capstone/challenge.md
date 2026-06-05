# Challenge 10 — Ship a Real Integration

Notes in [`solutions/`](./solutions/). Integration work on your Mac.

## Tasks
1. **Typed messages.** Replace the ad-hoc `"r,g,b"` string with JSON: send
   `{"r":0,"g":1,"b":0}` from SwiftUI (Codable → string) and parse it in `SceneBridge`
   with Unity's `JsonUtility`. Do the same for Unity → native (send a small JSON status).

2. **Command enum.** On the SwiftUI side, model commands as an enum
   (`enum UnityCommand { case setColor(Color), spawn, reset }`) with one `send()` method
   that maps each to a `sendMessage` call — so the call sites are type-safe.

3. **Reset round-trip.** Add a `Reset` command that zeroes Unity's score and clears
   spawned objects, and have Unity confirm by sending `score = 0` back. Verify the SwiftUI
   badge updates.

4. **Loading & errors.** Show a SwiftUI loading overlay until Unity sends its first
   "ready" message, and a friendly message if the framework fails to load.

5. **Stretch:** Drive a value continuously — a SwiftUI `Slider` that sends a rotation
   speed to Unity on change (throttle to avoid flooding `sendMessage`), and have Unity
   rotate the cube accordingly.

## Success criteria
- [ ] JSON messages both ways, parsed with `Codable` / `JsonUtility`.
- [ ] A type-safe `UnityCommand` enum drives all outbound calls.
- [ ] Reset zeroes state and Unity confirms via a callback.
- [ ] Loading/error states reflect Unity's lifecycle.

# Challenge 10 — Reference Notes

### 1. Typed JSON messages
SwiftUI → Unity:
```swift
struct ColorMsg: Codable { let r: Float; let g: Float; let b: Float }
func send(_ msg: ColorMsg) {
    let json = String(decoding: try! JSONEncoder().encode(msg), as: UTF8.self)
    UnityBridge.shared.send(toObject: "SceneBridge", method: "SetColorJSON", message: json)
}
```
Unity:
```csharp
[System.Serializable] public struct ColorMsg { public float r, g, b; }
public void SetColorJSON(string json) {
    var c = JsonUtility.FromJson<ColorMsg>(json);
    if (targetRenderer) targetRenderer.material.color = new Color(c.r, c.g, c.b);
}
```
Unity → native: build a small struct, `JsonUtility.ToJson(...)`, pass to
`NativeAPI.SendMessage(json)`, decode with `Codable` on the Swift side.

### 2. Command enum
```swift
enum UnityCommand {
    case setColor(Color), spawn, reset
    func send() {
        switch self {
        case .setColor(let c):
            UnityBridge.shared.send(toObject: "SceneBridge", method: "SetColor", message: CapstoneUnityView.rgbString(c))
        case .spawn:
            UnityBridge.shared.send(toObject: "SceneBridge", method: "Spawn", message: "")
        case .reset:
            UnityBridge.shared.send(toObject: "SceneBridge", method: "Reset", message: "")
        }
    }
}
// call site: UnityCommand.spawn.send()
```

### 3. Reset round-trip
Unity:
```csharp
public void Reset(string _) {
    score = 0;
    foreach (Transform t in spawnParent) Destroy(t.gameObject);
    NativeAPI.SendScore(score);     // confirm 0 back to native
}
```
SwiftUI badge observes `events.score` and updates to 0.

### 4. Loading & errors
```swift
@State private var ready = false
// observe the first "ready" message:
.onChange(of: events.lastMessage) { _, msg in if msg.contains("ready") { ready = true } }
.overlay { if !ready { ProgressView("Starting Unity…") } }
```
Wrap framework load in a do/catch (or check `UnityBridge.shared.rootView == nil`) and show
a fallback message if it fails.

### 5. Stretch — continuous slider (throttled)
```swift
@State private var speed: Double = 0
Slider(value: $speed, in: 0...360)
    .onChange(of: speed) { _, v in
        // throttle: only send a few times/sec
        UnityBridge.shared.send(toObject: "SceneBridge", method: "SetSpinSpeed", message: "\(Int(v))")
    }
```
Unity rotates in `Update` using the received speed. Throttle (e.g. a timer or a min delta)
so you don't flood `sendMessage` every frame.

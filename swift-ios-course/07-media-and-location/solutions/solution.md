# Challenge 07 — Reference Solution

### 1. Distance to place
```swift
func distanceText(to place: Place, from here: CLLocation, useMiles: Bool) -> String {
    let there = CLLocation(latitude: place.latitude, longitude: place.longitude)
    let meters = here.distance(from: there)                 // CLLocationDistance (meters)
    let m = Measurement(value: meters, unit: UnitLength.meters)
    let shown = useMiles ? m.converted(to: .miles) : m.converted(to: .kilometers)
    return shown.formatted(.measurement(width: .abbreviated, usage: .road))
}
```

### 2. Long-press to add a pin
```swift
MapReader { proxy in
    Map(position: $camera) { /* markers */ }
        .onLongPressGesture { /* get location from gesture */ }
        // Simpler: use a tap and convert:
        .onTapGesture { screenPoint in
            if let coord = proxy.convert(screenPoint, from: .local) {
                store.add(Place(name: "Dropped pin",
                                latitude: coord.latitude, longitude: coord.longitude))
            }
        }
}
```
`MapReader`'s `proxy.convert(_:from:)` turns a screen point into a `CLLocationCoordinate2D`.

### 3. Permission states
```swift
switch location.authorization {
case .notDetermined:
    Button("Enable location") { location.requestPermission() }
case .denied, .restricted:
    VStack {
        Text("Location is off. Enable it in Settings.")
        Button("Open Settings") {
            if let url = URL(string: UIApplication.openSettingsURLString) {
                UIApplication.shared.open(url)
            }
        }
    }
case .authorizedWhenInUse, .authorizedAlways:
    Text(location.lastLocation.map { "\($0.coordinate.latitude), \($0.coordinate.longitude)" } ?? "Locating…")
@unknown default:
    EmptyView()
}
```

### 4. Audio recording (stretch)
```swift
let session = AVAudioSession.sharedInstance()
try session.setCategory(.playAndRecord, mode: .default)
try session.setActive(true)
let url = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    .appendingPathComponent("memo.m4a")
let settings: [String: Any] = [
    AVFormatIDKey: Int(kAudioFormatMPEG4AAC),
    AVSampleRateKey: 12000, AVNumberOfChannelsKey: 1,
    AVEncoderAudioQualityKey: AVAudioQuality.high.rawValue
]
let recorder = try AVAudioRecorder(url: url, settings: settings)
recorder.record()    // ... recorder.stop(); then AudioPlayer().play(url: url)
```
Requires `NSMicrophoneUsageDescription`.

### 5. KVO on AVPlayer.status
```swift
let token = player.observe(\.status, options: [.new]) { p, _ in
    if p.status == .readyToPlay { print("ready") }
}
```
> AVFoundation predates async/await and is Obj-C; **KVO** is its idiomatic way to expose
> asynchronous state changes (`status`, `timeControlStatus`, buffering) — observe rather
> than poll. It's the same KVO from Module 03.

# Module 07 — Media & Location

**Goal:** use the heavier Objective-C-derived device frameworks — **Core Location**,
**MapKit**, **AVFoundation**, and **PhotosUI** — from SwiftUI, including the permission
model. ⏱️ ~3 h · 🎯 Prereq: 00–06 (especially the **delegate** pattern from 03).

---

## 1. Permissions first (or your app crashes)

iOS requires a **usage-description string** in `Info.plist` for each sensitive capability.
Missing it = the system denies access (and often crashes). Common keys:

| Capability | Info.plist key |
|------------|----------------|
| Location (in use) | `NSLocationWhenInUseUsageDescription` |
| Camera | `NSCameraUsageDescription` |
| Microphone | `NSMicrophoneUsageDescription` |
| Photo library | `NSPhotoLibraryUsageDescription` |

In `project.yml` (XcodeGen) add them as `INFOPLIST_KEY_*` settings; in Xcode add them in
the target's **Info** tab. The system shows the string in the permission prompt.

## 2. Core Location (delegate-based — classic Cocoa)

`CLLocationManager` reports via a **delegate** (`CLLocationManagerDelegate`) — exactly the
pattern from Module 03. You wrap it in an observable object for SwiftUI:
```swift
final class LocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    @Published var authorization: CLAuthorizationStatus = .notDetermined
    @Published var lastLocation: CLLocation?
    override init() { super.init(); manager.delegate = self }
    func request() { manager.requestWhenInUseAuthorization() }
    func locationManagerDidChangeAuthorization(_ m: CLLocationManager) { authorization = m.authorizationStatus }
    func locationManager(_ m: CLLocationManager, didUpdateLocations locs: [CLLocation]) { lastLocation = locs.last }
}
```
> Delegate-based managers commonly use `ObservableObject`/`@Published` (and `@StateObject`
> in the view). That's a deliberate contrast with the `@Observable` models from earlier —
> you'll see both in real code.

Simulate location in the **Simulator ▸ Features ▸ Location**.

## 3. MapKit in SwiftUI (iOS 17 Map)

```swift
Map(position: $camera) {
    ForEach(places) { p in
        Marker(p.name, coordinate: .init(latitude: p.latitude, longitude: p.longitude))
    }
    UserAnnotation()                 // the device location dot
}
.mapControls { MapUserLocationButton(); MapCompass() }
```
`Marker`/`Annotation` place pins; `MapCameraPosition` controls the viewport.
`CLLocationCoordinate2D` is the Obj-C coordinate type you'll pass around.

## 4. AVFoundation (audio)

```swift
final class AudioPlayer: NSObject, ObservableObject, AVAudioPlayerDelegate {
    private var player: AVAudioPlayer?
    @Published var isPlaying = false
    func play(url: URL) {
        player = try? AVAudioPlayer(contentsOf: url)
        player?.delegate = self; player?.play(); isPlaying = true
    }
    func audioPlayerDidFinishPlaying(_ p: AVAudioPlayer, successfully flag: Bool) { isPlaying = false }
}
```
AVFoundation also covers recording (`AVAudioRecorder`), video (`AVPlayer` /
`VideoPlayer` in SwiftUI), and camera capture (`AVCaptureSession`). Again: **delegate**
callbacks and KVO (`AVPlayer.status`) — the Obj-C heritage.

## 5. PhotosUI (the photo picker)

```swift
@State private var selection: PhotosPickerItem?
@State private var image: Image?

PhotosPicker("Choose photo", selection: $selection, matching: .images)
    .onChange(of: selection) {
        Task {
            if let data = try? await selection?.loadTransferable(type: Data.self),
               let ui = UIImage(data: data) { image = Image(uiImage: ui) }
        }
    }
```
`PhotosPicker` needs no permission prompt (the system UI runs out-of-process).

---

## Do the lab
Add a map of places, the device location, audio playback, and a photo picker to PlacesApp.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Reference code
[`code/LocationManager.swift`](./code/LocationManager.swift),
[`code/PlacesMapView.swift`](./code/PlacesMapView.swift),
[`code/AudioPlayer.swift`](./code/AudioPlayer.swift).

## Key terms
Info.plist usage strings · `CLLocationManager`/`CLLocationManagerDelegate` ·
`CLAuthorizationStatus` · `CLLocationCoordinate2D` · MapKit `Map`/`Marker`/`UserAnnotation` ·
`MapCameraPosition` · AVFoundation/`AVAudioPlayer` · `PhotosPicker`/`PhotosPickerItem`

**Next →** [Module 08: UIKit ↔ SwiftUI Interop](../08-uikit-swiftui-interop/)

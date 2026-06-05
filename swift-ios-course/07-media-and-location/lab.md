# Lab 07 — Maps, Location, Audio & Photos

**You'll:** add a map of places, the device location, a photo picker, and audio playback
to PlacesApp. ⏱️ ~70 min.

---

## Part A — Permissions
Add usage strings. In `apps/PlacesApp/project.yml`, under the target's `settings.base`:
```yaml
INFOPLIST_KEY_NSLocationWhenInUseUsageDescription: "Show your location near saved places."
INFOPLIST_KEY_NSPhotoLibraryUsageDescription: "Attach a photo to a place."
```
Re-run `xcodegen generate`. (Manual Xcode: target ▸ Info ▸ add the two keys.)

## Part B — A map tab
Add `code/PlacesMapView.swift` → `Sources/Views/PlacesMapView.swift`. Show it alongside
the list with a `TabView` in `PlaceListView` or the app root:
```swift
TabView {
    PlaceListView().tabItem { Label("List", systemImage: "list.bullet") }
    NavigationStack { PlacesMapView(places: store.places) }
        .tabItem { Label("Map", systemImage: "map") }
}
```
Run. ✅ The **Map** tab shows a pin (`Marker`) per place. Pinch/scroll to navigate.

## Part C — Device location
Add `code/LocationManager.swift` → `Sources/Services/LocationManager.swift`. In the map
screen:
```swift
@StateObject private var location = LocationManager()
// in body, e.g. a toolbar button:
.toolbar { Button("Locate") { location.requestPermission() } }
.onChange(of: location.authorization) { _, status in
    if status == .authorizedWhenInUse { location.start() }
}
```
Run, tap **Locate** → the system prompt appears (showing your usage string). Allow it,
then **Simulator ▸ Features ▸ Location ▸ Apple** (or a custom coordinate).
✅ The `MapUserLocationButton` recenters on the blue location dot; `location.lastLocation`
updates via the delegate callback.

## Part D — Photo picker
In `AddPlaceView` (or detail), add:
```swift
import PhotosUI
@State private var pick: PhotosPickerItem?
@State private var preview: Image?
// in the Form:
PhotosPicker("Add photo", selection: $pick, matching: .images)
preview?.resizable().scaledToFit().frame(height: 120)
// react:
.onChange(of: pick) {
    Task {
        if let data = try? await pick?.loadTransferable(type: Data.self),
           let ui = UIImage(data: data) { preview = Image(uiImage: ui) }
    }
}
```
Run → tap **Add photo** → the system photo picker appears (no permission prompt needed),
pick an image → it previews. ✅ `PhotosPicker` + async `loadTransferable`.

## Part E — Audio playback
Add `code/AudioPlayer.swift` → `Sources/Services/AudioPlayer.swift`. Add a short sound to
the app (drag an `.mp3`/`.m4a` into the project, or use any bundled clip), then:
```swift
@StateObject private var audio = AudioPlayer()
Button(audio.isPlaying ? "Stop" : "Play sound") {
    if audio.isPlaying { audio.stop() }
    else if let url = Bundle.main.url(forResource: "chime", withExtension: "m4a") {
        audio.play(url: url)
    }
}
```
Run → tap **Play** → the clip plays; the button flips to **Stop** and back when it
finishes (the delegate callback). ✅ AVFoundation playback.

> No audio file handy? Skip Part E or use any short clip; the pattern is the point.

## What you learned
- Permission usage strings are mandatory for location/photos/mic/camera.
- Core Location via a **delegate** wrapped in `ObservableObject`.
- MapKit's SwiftUI `Map` with `Marker`/`UserAnnotation`.
- `PhotosPicker` for images; `AVAudioPlayer` (delegate) for sound.

➡️ **[challenge.md](./challenge.md)** then [Module 08](../08-uikit-swiftui-interop/).

# Challenge 07 — Device Features

Notes/solution in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Distance to place.** Using `location.lastLocation`, compute and display each place's
   distance from the device (`CLLocation.distance(from:)`), formatted with the
   `useMiles` setting from Module 05.

2. **Tap to add at a coordinate.** On the map, let the user long-press to drop a pin and
   create a new `Place` at that coordinate (hint: `MapReader` + `convert(_:from:)` or a
   map tap gesture to get a `CLLocationCoordinate2D`).

3. **Permission states.** Handle all `CLAuthorizationStatus` cases: show a "enable in
   Settings" message when `.denied`, request when `.notDetermined`, and show location
   when authorized. (Add a button that deep-links to Settings via
   `UIApplication.shared.open(URL(string: UIApplication.openSettingsURLString)!)`.)

4. **Audio recording (stretch).** Use `AVAudioRecorder` to record a voice memo for a
   place (requires `NSMicrophoneUsageDescription`), then play it back with `AudioPlayer`.

5. **KVO observation (tie-back).** Observe an `AVPlayer`'s `status` with KVO (Module 03)
   and log when it becomes `.readyToPlay`. Why does AVFoundation use KVO here?

## Success criteria
- [ ] Per-place distance shown, unit-aware.
- [ ] Long-press on the map creates a place at that coordinate.
- [ ] All authorization states handled, including a Settings deep-link when denied.
- [ ] (Stretch) Record + playback works with the mic permission.

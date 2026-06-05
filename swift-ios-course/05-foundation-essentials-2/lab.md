# Lab 05 — Networking, Caching & Settings in PlacesApp

**You'll:** load real data over the network, cache it to disk, and add a persisted
setting. ⏱️ ~55 min. Work in your PlacesApp (from Module 02).

> The app talks to `https://jsonplaceholder.typicode.com/users` (a stable free test API).
> The Simulator has network access by default.

---

## Part A — Add the networking files
Add to your PlacesApp `Sources/`:
- `code/PlaceService.swift` → `Sources/Services/PlaceService.swift`
- `code/PlaceStore+Networking.swift` → `Sources/Stores/PlaceStore+Networking.swift`

(Both files are in this module's `code/` folder.)

## Part B — Load on appear + pull to refresh
In `PlaceListView.swift`, start with an empty store and load from the network. Change the
app entry to start empty:
```swift
// PlacesAppApp.swift
@State private var store = PlaceStore(places: [])
```
Then in `PlaceListView`'s `body`, add to the `List`:
```swift
.task { await store.reload() }          // runs when the view first appears
.refreshable { await store.reload() }    // pull-to-refresh
.overlay {
    if store.places.isEmpty { ProgressView("Loading…") }
}
```
Run. ✅ Expected: a brief "Loading…", then ~10 places (names like "Leanne Graham") appear
with notes (the company catch-phrase) and real coordinates. Pull down to refresh.

## Part C — Prove the disk cache (offline)
1. Run once with network on so the cache is written.
2. In the Simulator, turn off networking: **Simulator** keeps the Mac's network, so
   instead simulate failure — temporarily change the endpoint in `PlaceService` to a bad
   host (e.g. `https://jsonplaceholder.invalid/users`).
3. Run again. ✅ The console logs "reload failed … using cache" and the list still shows
   the **previously cached** places. Restore the correct endpoint.

> This is the everyday Foundation stack: `URLSession` + `Codable` + `FileManager`.

## Part D — A persisted setting with @AppStorage
Show coordinates in km or miles based on a setting. Add a settings toggle:
```swift
// somewhere in PlaceListView toolbar or a settings sheet:
@AppStorage("useMiles") private var useMiles = false
// in the toolbar:
ToolbarItem(placement: .topBarLeading) {
    Toggle(isOn: $useMiles) { Image(systemName: "ruler") }
}
```
In `PlaceDetailView`, read it and convert a stored distance for display:
```swift
@AppStorage("useMiles") private var useMiles = false
// example: show a Measurement converted on the fly
let km = Measurement(value: 5, unit: UnitLength.kilometers)
Text(useMiles ? km.converted(to: .miles).formatted() : km.formatted())
```
Toggle it, force-quit and relaunch the app. ✅ The setting persists (it's in
`UserDefaults`).

## Part E — Inspect the JSON decoding
Put a breakpoint in `PlaceService.fetchPlaces()` after `decode`, run, and inspect the
decoded array in the debugger — confirm names/coords. Note how nested `Decodable` structs
(`Address`, `Geo`, `Company`) mirror the JSON shape, and `lat`/`lng` arrive as **strings**
(hence `Double(...)`).

## What you learned
- `Codable` + `URLSession` to fetch and decode JSON (async/await, status checks).
- A `FileManager` disk cache with graceful offline fallback.
- `@AppStorage`/`UserDefaults` for persisted settings.
- Keeping UI updates on `@MainActor`.

➡️ **[challenge.md](./challenge.md)** then [Module 06](../06-core-data/).

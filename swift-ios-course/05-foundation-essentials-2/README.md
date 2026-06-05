# Module 05 — Foundation Essentials II (App Plumbing)

**Goal:** the Foundation APIs that make an app *do* things — JSON `Codable`, **URLSession**
networking, `UserDefaults`, **NotificationCenter**, and `FileManager` — wired into
PlacesApp. ⏱️ ~2.5 h · 🎯 Prereq: 00–04.

---

## 1. Codable — JSON without ceremony

`Codable` (= `Encodable` + `Decodable`) is the modern replacement for
`NSJSONSerialization`. Conform your model and the compiler synthesizes encoding/decoding:
```swift
struct Place: Codable { var name: String; var latitude: Double; var longitude: Double }

let data = try JSONEncoder().encode(place)
let place = try JSONDecoder().decode(Place.self, from: data)
```
Map mismatched names with `CodingKeys`:
```swift
struct User: Decodable {
    let fullName: String
    enum CodingKeys: String, CodingKey { case fullName = "name" }
}
```
Decode nested JSON with nested `Decodable` structs (as the lab's `RemoteUser` does).

## 2. URLSession — networking (async/await)

```swift
let url = URL(string: "https://api.example.com/items")!
let (data, response) = try await URLSession.shared.data(from: url)
guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
    throw URLError(.badServerResponse)
}
let items = try JSONDecoder().decode([Item].self, from: data)
```
- `data(from:)` / `data(for: URLRequest)` are the async entry points.
- Build requests with `URLRequest` (method, headers, body) for POST/PUT.
- Always check the `HTTPURLResponse.statusCode`.
- Networking is **off the main thread**; hop back with `@MainActor` before touching UI.

## 3. UserDefaults — small persistent settings

```swift
UserDefaults.standard.set(true, forKey: "showImperialUnits")
let on = UserDefaults.standard.bool(forKey: "showImperialUnits")
```
In SwiftUI, bind directly with `@AppStorage`:
```swift
@AppStorage("showImperialUnits") private var imperial = false
Toggle("Imperial units", isOn: $imperial)     // persists automatically
```
For **settings**, not for large data (use files/Core Data for that).

## 4. NotificationCenter — system & app events

Subscribe to system events (keyboard, app lifecycle) or your own:
```swift
NotificationCenter.default.addObserver(forName: UIApplication.didBecomeActiveNotification,
    object: nil, queue: .main) { _ in /* refresh */ }
```
In SwiftUI, `.onReceive(NotificationCenter.default.publisher(for:))` bridges it to a view.

## 5. FileManager — the filesystem & caching

Apps write to sandboxed directories:
```swift
let dir = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
let file = dir.appendingPathComponent("places.json")
try JSONEncoder().encode(places).write(to: file)         // cache to disk
let cached = try? JSONDecoder().decode([Place].self, from: Data(contentsOf: file))
```
- **Documents** — user data, backed up.
- **Caches** — regenerable data, may be purged.
- `NSCache` is an in-memory cache (key/value, auto-evicting).

## 6. Putting it together (PlacesApp)

The lab gives PlacesApp a `PlaceService` (URLSession + Codable) that loads places from a
public test API, a pull-to-refresh, an offline **disk cache** via `FileManager`, and a
**units setting** via `@AppStorage`.

```mermaid
flowchart LR
  api[(Test API JSON)] -->|URLSession + Codable| svc[PlaceService]
  svc --> store[@Observable PlaceStore]
  store --> ui[SwiftUI List]
  store <-->|FileManager cache| disk[(places.json)]
  setting[@AppStorage units] --> ui
```

---

## Do the lab
Add networking, caching, and a setting to PlacesApp; load real data with pull-to-refresh.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Reference code
[`code/PlaceService.swift`](./code/PlaceService.swift),
[`code/PlaceStore+Networking.swift`](./code/PlaceStore+Networking.swift).

## Key terms
`Codable`/`CodingKeys` · `JSONEncoder`/`JSONDecoder` · `URLSession`/`URLRequest`/
`HTTPURLResponse` · `@MainActor` · `UserDefaults`/`@AppStorage` · NotificationCenter ·
`FileManager` (Documents/Caches) · `NSCache`

**Next →** [Module 06: Core Data & SwiftData](../06-core-data/)

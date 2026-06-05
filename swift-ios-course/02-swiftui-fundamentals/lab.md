# Lab 02 — Build & Run PlacesApp

**You'll:** get the SwiftUI through-line app running — list, detail, and add — and
understand how state flows. ⏱️ ~55 min.

---

## Part A — Open the app
**XcodeGen route (recommended):**
```bash
brew install xcodegen          # one-time
cd swift-ios-course/apps/PlacesApp
xcodegen generate
open PlacesApp.xcodeproj
```
**Manual route:** Xcode ▸ New ▸ App (SwiftUI, name `PlacesApp`), delete the generated
`ContentView.swift`, then add every file under `apps/PlacesApp/Sources/` to the target
(File ▸ Add Files…, "Create groups").

Pick an **iPhone 16** simulator, press **Run** (`Cmd+R`).

✅ Expected: a **Places** list with two sample rows ("Golden Gate Park", "Ferry Building").

## Part B — Read the data flow
Open the files and trace how state moves:
1. `PlacesAppApp.swift` creates a `PlaceStore` with `@State` and injects it via
   `.environment(store)`.
2. `PlaceListView` reads it with `@Environment(PlaceStore.self)` and renders `store.places`.
3. Because `PlaceStore` is `@Observable`, adding/removing a place **automatically**
   refreshes the list — no manual reload.

## Part C — Navigate
Tap a row. ✅ `NavigationLink(value: place)` + `navigationDestination(for: Place.self)`
pushes `PlaceDetailView`, showing notes + coordinates. Tap **Back**.

## Part D — Add a place (state + sheets + bindings)
1. Tap **+** (top-right). The `AddPlaceView` sheet appears.
2. Type a name (notes optional). Note **Save** is disabled until the name is non-empty
   (`.disabled(!canSave)`).
3. Tap **Save**. ✅ The sheet dismisses (`@Environment(\.dismiss)`) and your new place
   appears in the list instantly — that's `@Observable` + `store.add(...)` at work.

## Part E — Swipe to delete
Swipe a row left → **Delete**. ✅ `.onDelete { store.delete(at: $0) }` removes it and the
list animates. Delete everything → the `ContentUnavailableView` empty state shows.

## Part F — Use previews
Open `PlaceListView.swift`, show the canvas (`Option+Cmd+Return`). The `#Preview` renders
the list with a fresh store. Change `Text(place.name).font(.headline)` to `.font(.title3)`
and watch the preview update without running the app.

## Part G — Make a small change yourself
Add a relative count to the navigation title:
```swift
.navigationTitle("Places (\(store.places.count))")
```
Run → the title reflects the live count as you add/delete. ✅ State drives the UI.

## What you learned
- Views are value types; **state drives rendering**.
- `@Observable` + `@Environment` share a model across screens with automatic updates.
- `List`/`ForEach`/`.onDelete`, `NavigationStack`/`NavigationLink`, `.sheet`, `Form`,
  bindings (`$`), and `#Preview`.

➡️ **[challenge.md](./challenge.md)** then [Module 03](../03-objc-heritage-bridging/).

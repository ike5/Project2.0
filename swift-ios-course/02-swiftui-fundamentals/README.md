# Module 02 — SwiftUI Fundamentals

**Goal:** build real screens with SwiftUI — views, state, layout, lists, and navigation —
and stand up the first version of **PlacesApp**. ⏱️ ~2.5 h · 🎯 Prereq: 00–01.

> Full reference: [cheatsheets/swiftui.md](../cheatsheets/swiftui.md).

---

## 1. Views are values

A SwiftUI `View` is a **struct** with a `body`. SwiftUI calls `body` to get a description
of the UI, then renders it. You never mutate views — you change **state** and SwiftUI
recomputes `body`.

```swift
struct GreetingView: View {
    let name: String
    var body: some View {
        Text("Hello, \(name)!")
            .font(.title)
            .padding()
    }
}
```
`some View` = "a specific concrete View I won't spell out." Modifiers (`.font`, `.padding`)
each return a *new* view.

## 2. Layout

```swift
VStack(alignment: .leading, spacing: 8) {   // vertical
    Text("Title").font(.headline)
    HStack { Image(systemName: "star"); Text("Subtitle") }   // horizontal
}
ZStack { Color.blue; Text("On top") }        // layered
```
Reach for `VStack`/`HStack`/`ZStack`, `Spacer`, `Divider`, `ScrollView`, and `Grid`.
Use `Lazy*` stacks inside scroll views for long content.

## 3. State (the @-wrappers)

| Wrapper | Use for |
|---------|---------|
| `@State` | local mutable state owned by this view (value types, or an `@Observable` model) |
| `@Binding` | a two-way reference to state owned by a parent (`$value`) |
| `@Observable` class + `@State` | a reference-type model whose changes refresh the UI (iOS 17+) |
| `@Environment` | read injected values / models from the hierarchy |
| `@AppStorage` | a value bound to `UserDefaults` |

```swift
struct CounterView: View {
    @State private var count = 0
    var body: some View {
        Button("Count: \(count)") { count += 1 }   // tapping mutates state -> body re-runs
    }
}
```
Pass a binding with `$`:
```swift
TextField("Name", text: $name)
Toggle("On", isOn: $isOn)
```

### Observable models (iOS 17+)
```swift
@Observable final class PlaceStore { var places: [Place] = [] }
// own it:
@State private var store = PlaceStore()
// inject it:
SomeView().environment(store)
// read it elsewhere:
@Environment(PlaceStore.self) private var store
```
This is what `PlacesApp` uses. (Pre-iOS-17 used `ObservableObject` + `@Published` +
`@StateObject`/`@ObservedObject` — you'll still see those in older code.)

## 4. Lists & identity

```swift
List {
    ForEach(store.places) { place in Text(place.name) }
        .onDelete { store.delete(at: $0) }
}
```
Rows need stable identity — conform your model to **`Identifiable`** (an `id`).

## 5. Navigation

```swift
NavigationStack {
    List(store.places) { place in
        NavigationLink(value: place) { Text(place.name) }
    }
    .navigationTitle("Places")
    .navigationDestination(for: Place.self) { place in PlaceDetailView(place: place) }
}
```
`NavigationLink(value:)` + `navigationDestination(for:)` is the modern, data-driven
navigation API (the model must be `Hashable`).

## 6. Sheets, toolbars, forms

```swift
.toolbar { ToolbarItem(placement: .primaryAction) { Button { showingAdd = true } label: { Image(systemName: "plus") } } }
.sheet(isPresented: $showingAdd) { AddPlaceView() }

Form { TextField("Name", text: $name); Toggle("Favorite", isOn: $fav) }
```

## 7. Previews — your feedback loop

```swift
#Preview { PlaceListView().environment(PlaceStore()) }
```
The Xcode canvas renders previews live as you type. Use them constantly.

---

## Do the lab
Build and run **PlacesApp**: a list, a detail screen, and an add-place sheet wired to an
`@Observable` store. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Reference
[`apps/PlacesApp`](../apps/PlacesApp/) — the app you'll run.

## Key terms
`View`/`body`/`some View` · modifier · `VStack`/`HStack`/`ZStack` · `@State`/`@Binding` ·
`@Observable`/`@Environment` · `Identifiable` · `List`/`ForEach`/`.onDelete` ·
`NavigationStack`/`NavigationLink`/`navigationDestination` · `.sheet` · `Form` · `#Preview`

**Next →** [Module 03: Objective-C Heritage & Bridging](../03-objc-heritage-bridging/)

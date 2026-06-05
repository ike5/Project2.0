# Challenge 02 — Reference Solution

### 1. Edit a place
Add to `PlaceStore`:
```swift
func update(_ place: Place) {
    if let i = places.firstIndex(where: { $0.id == place.id }) {
        places[i] = place
    }
}
```
A reusable edit form (works for add *and* edit):
```swift
struct EditPlaceView: View {
    @Environment(PlaceStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    @State var draft: Place                     // a mutable copy
    let isNew: Bool

    var body: some View {
        NavigationStack {
            Form {
                TextField("Name", text: $draft.name)
                TextField("Notes", text: $draft.notes, axis: .vertical)
            }
            .navigationTitle(isNew ? "New Place" : "Edit Place")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        if isNew { store.add(draft) } else { store.update(draft) }
                        dismiss()
                    }
                    .disabled(draft.name.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
        }
    }
}
```
In `PlaceDetailView`, add `@State private var editing = false` and a toolbar Edit button
presenting `EditPlaceView(draft: place, isNew: false)` in a `.sheet`.

### 2. Favorites
```swift
// Place.swift
var isFavorite = false
```
Row star (writes back through the store):
```swift
Button {
    var p = place; p.isFavorite.toggle(); store.update(p)
} label: {
    Image(systemName: place.isFavorite ? "star.fill" : "star")
}
.buttonStyle(.borderless)   // so the row's NavigationLink still works
```
Filter:
```swift
@State private var showFavoritesOnly = false
var shown: [Place] { showFavoritesOnly ? store.places.filter(\.isFavorite) : store.places }
// Toolbar: Toggle("Favorites", isOn: $showFavoritesOnly)
```

### 3. Search
```swift
@State private var query = ""
var filtered: [Place] {
    query.isEmpty ? shown : shown.filter { $0.name.localizedCaseInsensitiveContains(query) }
}
// on the List:
.searchable(text: $query)
// iterate `filtered` instead of store.places
```

### 4. Sort
```swift
enum SortKey { case name, recent }
@State private var sortKey: SortKey = .recent
var sorted: [Place] {
    switch sortKey {
    case .name: return filtered.sorted { $0.name < $1.name }
    case .recent: return filtered                     // newest appended last; reverse if desired
    }
}
// Toolbar menu:
Menu {
    Picker("Sort", selection: $sortKey) {
        Text("Name").tag(SortKey.name); Text("Recent").tag(SortKey.recent)
    }
} label: { Image(systemName: "arrow.up.arrow.down") }
```

### 5. Reusable row with a binding (stretch)
```swift
struct PlaceRow: View {
    let place: Place
    @Binding var isFavorite: Bool
    var body: some View {
        HStack {
            VStack(alignment: .leading) { Text(place.name).font(.headline) }
            Spacer()
            Button { isFavorite.toggle() } label: {
                Image(systemName: isFavorite ? "star.fill" : "star")
            }.buttonStyle(.borderless)
        }
    }
}
```
> Because `Place` is a value type, "editing" means replacing it in the store by `id`.
> That immutability is intentional — it's what makes SwiftUI's diffing predictable.

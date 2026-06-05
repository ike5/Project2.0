# Challenge 06 — Reference Solution

### 1. Edit + persist (SwiftData)
```swift
struct EditPlaceItemView: View {
    @Bindable var place: PlaceItem            // @Bindable gives $-bindings to a @Model
    var body: some View {
        Form {
            TextField("Name", text: $place.name)
            TextField("Notes", text: $place.notes, axis: .vertical)
        }
        // No save call needed — SwiftData autosaves the context.
    }
}
```
> `@Bindable` is the SwiftData/Observation way to bind to a reference model's properties.

### 2. Seed once
```swift
@AppStorage("seeded") private var seeded = false
.task {
    guard !seeded else { return }
    for p in PlaceStore.sample { context.insert(PlaceItem(name: p.name, notes: p.notes,
                                                          latitude: p.latitude, longitude: p.longitude)) }
    seeded = true
}
```

### 3. Relationship
SwiftData:
```swift
@Model final class Tag { var name: String; init(name: String) { self.name = name } }

@Model final class PlaceItem {
    // ...
    @Relationship(deleteRule: .nullify) var tags: [Tag] = []
}
// usage: place.tags.append(Tag(name: "park"))
```
Core Data equivalent: add an `NSRelationshipDescription` named `tags` on `CDPlace` with
`destinationEntity = CDTag`, `maxCount = 0` (to-many), and a matching inverse
relationship on `CDTag` — plus a delete rule. (This is why the visual editor is handy.)

### 4. Predicate
SwiftData (type-safe):
```swift
@State private var query = ""
@Query private var places: [PlaceItem]
var filtered: [PlaceItem] {
    query.isEmpty ? places
        : places.filter { $0.name.localizedCaseInsensitiveContains(query) }
}
// or a dynamic @Query with #Predicate built from `query`
```
Core Data equivalent:
```swift
request.predicate = NSPredicate(format: "name CONTAINS[cd] %@", query)
```
> `#Predicate` is compile-checked against your model; `NSPredicate(format:)` is a string
> parsed at runtime (typos crash at runtime). Same capability, different safety.

### 5. Stretch — offline-first via the store
```swift
@MainActor func reload(using service: PlaceService = PlaceService(), context: ModelContext) async {
    guard let fetched = try? await service.fetchPlaces() else { return }
    let existingIds = Set((try? context.fetch(FetchDescriptor<PlaceItem>()))?.map(\.id) ?? [])
    for p in fetched where !existingIds.contains(p.id) {
        context.insert(PlaceItem(name: p.name, notes: p.notes, latitude: p.latitude, longitude: p.longitude))
    }
}
```
> Now the SwiftData store *is* the cache — the app shows persisted data immediately and
> merges new network results, no separate JSON file needed.

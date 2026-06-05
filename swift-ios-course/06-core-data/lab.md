# Lab 06 — Persist PlacesApp

**You'll:** persist places so they survive app relaunch — first the **SwiftData** path
(quick), then see the **Core Data** equivalent. ⏱️ ~70 min.

> We lead with SwiftData because it needs no binary model file and is the modern default,
> then map it back to the Core Data concepts you'll meet in existing apps.

---

## Path A — SwiftData (primary)

### A1. Add the model
Add `code/SwiftDataPlace.swift` → `Sources/Models/PlaceItem.swift`.

### A2. Install the container at the app root
```swift
// PlacesAppApp.swift
import SwiftData

@main struct PlacesAppApp: App {
    var body: some Scene {
        WindowGroup { PersistentListView() }
            .modelContainer(for: PlaceItem.self)     // creates/loads the store
    }
}
```

### A3. A persisted list view
Create `Sources/Views/PersistentListView.swift`:
```swift
import SwiftUI
import SwiftData

struct PersistentListView: View {
    @Environment(\.modelContext) private var context
    @Query(sort: \PlaceItem.name) private var places: [PlaceItem]
    @State private var newName = ""

    var body: some View {
        NavigationStack {
            List {
                ForEach(places) { p in Text(p.name) }
                    .onDelete { idx in idx.map { places[$0] }.forEach(context.delete) }
            }
            .navigationTitle("Places (\(places.count))")
            .toolbar {
                ToolbarItem(placement: .bottomBar) {
                    HStack {
                        TextField("New place", text: $newName)
                        Button("Add") {
                            context.insert(PlaceItem(name: newName))
                            newName = ""
                        }.disabled(newName.isEmpty)
                    }
                }
            }
        }
    }
}
```
> SwiftData **autosaves** by default, so inserts/deletes persist without an explicit save.

### A4. Prove persistence
Run. Add a few places. **Stop** the app (or force-quit in the Simulator), then **Run**
again. ✅ Your places are still there — they're in the SwiftData store on disk. `@Query`
re-loads and live-updates the list.

### A5. A type-safe query
Filter with `#Predicate`:
```swift
@Query(filter: #Predicate<PlaceItem> { $0.name.contains("a") }, sort: \PlaceItem.name)
private var aPlaces: [PlaceItem]
```
✅ Only matching places appear — and it's compile-checked, unlike `NSPredicate` strings.

---

## Path B — Core Data (the classic equivalent)

Read [`code/CoreDataStack.swift`](./code/CoreDataStack.swift) — it builds a `CDPlace`
entity in code and exposes `CoreDataStack.shared`. The same CRUD, the Objective-C way:
```swift
let context = CoreDataStack.shared.viewContext
let place = CDPlace(context: context)
place.id = UUID(); place.name = "Park"; place.latitude = 1; place.longitude = 2
try context.save()                                   // persist

let results = try context.fetch(CDPlace.fetchAll())  // NSFetchRequest + NSSortDescriptor
print(results.map(\.name))
```
In SwiftUI you'd inject the context and use `@FetchRequest`:
```swift
ContentView()
    .environment(\.managedObjectContext, CoreDataStack.shared.viewContext)

@FetchRequest(sortDescriptors: [SortDescriptor(\CDPlace.name)])
private var places: FetchedResults<CDPlace>
```
✅ Note what's *more* work than SwiftData: explicit `save()`, `NSFetchRequest`,
`NSSortDescriptor`, string-keyed `NSPredicate`. That's the Objective-C heritage — and
what most existing codebases you'll support look like.

---

## Compare
| | SwiftData | Core Data |
|---|-----------|-----------|
| Model | `@Model` class | `.xcdatamodeld` / code model |
| Save | autosave | explicit `context.save()` |
| Query | `@Query` + `#Predicate` | `@FetchRequest` + `NSPredicate` |
| Boilerplate | minimal | more |

## What you learned
- Persist with SwiftData (`@Model`, `modelContainer`, `@Query`, `#Predicate`) — survives relaunch.
- The Core Data stack it's built on (`NSManagedObjectContext`, `NSFetchRequest`,
  `@FetchRequest`) and why existing apps look the way they do.

➡️ **[challenge.md](./challenge.md)** then [Module 07](../07-media-and-location/).

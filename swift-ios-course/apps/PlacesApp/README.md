# PlacesApp

The SwiftUI through-line app for the course. It starts as an in-memory list of "places"
(Module 02) and grows across modules: networking (05), Core Data persistence (06),
maps & media (07), a UIKit bridge (08), and an embedded Unity view (09–10).

## Open it

**Option A — XcodeGen (reproducible, text-based):**
```bash
brew install xcodegen          # one-time
cd swift-ios-course/apps/PlacesApp
xcodegen generate              # reads project.yml -> PlacesApp.xcodeproj
open PlacesApp.xcodeproj
```
Pick an **iPhone 16** simulator and press **Run** (`Cmd+R`).

**Option B — manual:** Xcode ▸ New ▸ App (SwiftUI), then add the files under `Sources/`
to the target (drag them in, "Create groups"). Delete Xcode's default `ContentView`.

## Structure (after Module 02)
```
Sources/
├── PlacesAppApp.swift        @main entry; owns the PlaceStore
├── Models/Place.swift        value-type model (Identifiable/Hashable/Codable)
├── Stores/PlaceStore.swift   @Observable in-memory store
└── Views/
    ├── PlaceListView.swift    list + navigation + add button
    ├── PlaceDetailView.swift  detail screen
    └── AddPlaceView.swift     add form (sheet)
```

## How later modules extend it
Each module's `code/` folder contains the **new or changed** files for that step; the
lab tells you exactly which to add/replace. This keeps each stage runnable rather than
maintaining one giant evolving project.

> `PlacesApp.xcodeproj/` is git-ignored — it's generated from `project.yml`.

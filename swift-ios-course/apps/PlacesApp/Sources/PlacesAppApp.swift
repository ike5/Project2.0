import SwiftUI

// The app entry point. @main marks the type that launches the app — SwiftUI's
// replacement for a UIApplicationDelegate / main() for most apps.
@main
struct PlacesAppApp: App {
    // Own the data store for the app's lifetime. @State holding an @Observable model
    // (iOS 17+) keeps it alive and observed.
    @State private var store = PlaceStore()

    var body: some Scene {
        WindowGroup {
            PlaceListView()
                .environment(store)        // inject the store into the view hierarchy
        }
    }
}

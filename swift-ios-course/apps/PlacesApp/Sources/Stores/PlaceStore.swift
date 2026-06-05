import Foundation
import Observation

// @Observable (iOS 17+) makes this reference-type model observable by SwiftUI: any view
// that reads `places` re-renders when it changes. This is the modern replacement for
// ObservableObject/@Published.
@Observable
final class PlaceStore {
    var places: [Place]

    init(places: [Place] = PlaceStore.sample) {
        self.places = places
    }

    func add(_ place: Place) {
        places.append(place)
    }

    func delete(at offsets: IndexSet) {
        places.remove(atOffsets: offsets)
    }

    static let sample: [Place] = [
        Place(name: "Golden Gate Park", notes: "Big urban park",
              latitude: 37.7694, longitude: -122.4862),
        Place(name: "Ferry Building", notes: "Marketplace by the bay",
              latitude: 37.7955, longitude: -122.3937),
    ]
}

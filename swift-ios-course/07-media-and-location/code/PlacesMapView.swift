import SwiftUI
import MapKit

// A map of the places plus the device's location dot (iOS 17 Map API).
struct PlacesMapView: View {
    let places: [Place]
    @State private var camera: MapCameraPosition = .automatic

    var body: some View {
        Map(position: $camera) {
            ForEach(places) { place in
                Marker(place.name,
                       coordinate: CLLocationCoordinate2D(latitude: place.latitude,
                                                          longitude: place.longitude))
            }
            UserAnnotation()                         // shows the current location
        }
        .mapControls {
            MapUserLocationButton()
            MapCompass()
            MapScaleView()
        }
        .navigationTitle("Map")
    }
}

#Preview {
    NavigationStack {
        PlacesMapView(places: PlaceStore.sample)
    }
}

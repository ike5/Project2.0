import SwiftUI

struct PlaceDetailView: View {
    let place: Place

    var body: some View {
        List {
            Section("Notes") {
                Text(place.notes.isEmpty ? "No notes yet." : place.notes)
                    .foregroundStyle(place.notes.isEmpty ? .secondary : .primary)
            }
            Section("Coordinates") {
                LabeledContent("Latitude",
                               value: place.latitude,
                               format: .number.precision(.fractionLength(4)))
                LabeledContent("Longitude",
                               value: place.longitude,
                               format: .number.precision(.fractionLength(4)))
            }
        }
        .navigationTitle(place.name)
        .navigationBarTitleDisplayMode(.inline)
    }
}

#Preview {
    NavigationStack {
        PlaceDetailView(place: PlaceStore.sample[0])
    }
}

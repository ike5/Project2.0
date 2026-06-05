import SwiftUI

struct PlaceListView: View {
    @Environment(PlaceStore.self) private var store
    @State private var showingAdd = false

    var body: some View {
        NavigationStack {
            List {
                ForEach(store.places) { place in
                    NavigationLink(value: place) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text(place.name).font(.headline)
                            if !place.notes.isEmpty {
                                Text(place.notes)
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                                    .lineLimit(1)
                            }
                        }
                    }
                }
                .onDelete { store.delete(at: $0) }
            }
            .navigationTitle("Places")
            .navigationDestination(for: Place.self) { place in
                PlaceDetailView(place: place)
            }
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showingAdd = true
                    } label: {
                        Label("Add", systemImage: "plus")
                    }
                }
            }
            .sheet(isPresented: $showingAdd) {
                AddPlaceView()
            }
            .overlay {
                if store.places.isEmpty {
                    ContentUnavailableView("No Places", systemImage: "mappin.slash",
                                           description: Text("Tap + to add one."))
                }
            }
        }
    }
}

#Preview {
    PlaceListView()
        .environment(PlaceStore())
}

import Foundation

// A value-type model. Identifiable for List/ForEach; Hashable for NavigationLink(value:);
// Codable so later modules can persist/transmit it.
struct Place: Identifiable, Hashable, Codable {
    var id: UUID = UUID()
    var name: String
    var notes: String = ""
    var latitude: Double = 0
    var longitude: Double = 0
}

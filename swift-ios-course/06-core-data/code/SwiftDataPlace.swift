import Foundation
import SwiftData

// The SwiftData counterpart: a persisted model with zero boilerplate and no binary model
// file. SwiftData is built on Core Data but is Swift-native (iOS 17+).
@Model
final class PlaceItem {
    var id: UUID
    var name: String
    var notes: String
    var latitude: Double
    var longitude: Double
    var createdAt: Date

    init(id: UUID = UUID(),
         name: String,
         notes: String = "",
         latitude: Double = 0,
         longitude: Double = 0,
         createdAt: Date = .now) {
        self.id = id
        self.name = name
        self.notes = notes
        self.latitude = latitude
        self.longitude = longitude
        self.createdAt = createdAt
    }
}

import Foundation

/// A simple model used across the course's networking/persistence examples.
public struct Place: Codable, Equatable {
    public var name: String
    public var latitude: Double
    public var longitude: Double

    public init(name: String, latitude: Double, longitude: Double) {
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
    }
}

/// Codable JSON helpers (the modern replacement for NSJSONSerialization).
public enum JSONKata {

    /// Encode to a JSON string with sorted keys (stable output).
    public static func encode(_ place: Place) throws -> String {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        let data = try encoder.encode(place)
        return String(decoding: data, as: UTF8.self)
    }

    /// Decode a `Place` from a JSON string.
    public static func decode(_ json: String) throws -> Place {
        try JSONDecoder().decode(Place.self, from: Data(json.utf8))
    }
}

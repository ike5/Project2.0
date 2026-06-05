import Foundation

// Loads places from a public test API (jsonplaceholder) using URLSession + Codable.
// The remote "users" happen to carry a name + geo coordinates, which we map to Place.
struct PlaceService {
    var session: URLSession = .shared
    var endpoint = URL(string: "https://jsonplaceholder.typicode.com/users")!

    func fetchPlaces() async throws -> [Place] {
        let (data, response) = try await session.data(from: endpoint)
        guard let http = response as? HTTPURLResponse,
              (200..<300).contains(http.statusCode) else {
            throw URLError(.badServerResponse)
        }
        let users = try JSONDecoder().decode([RemoteUser].self, from: data)
        return users.map { user in
            Place(name: user.name,
                  notes: user.company.catchPhrase,
                  latitude: Double(user.address.geo.lat) ?? 0,
                  longitude: Double(user.address.geo.lng) ?? 0)
        }
    }
}

// The remote JSON shape (only the fields we need). Nested Decodable structs map nested JSON.
private struct RemoteUser: Decodable {
    let name: String
    let address: Address
    let company: Company

    struct Address: Decodable { let geo: Geo }
    struct Geo: Decodable { let lat: String; let lng: String }   // API returns strings
    struct Company: Decodable { let catchPhrase: String }
}

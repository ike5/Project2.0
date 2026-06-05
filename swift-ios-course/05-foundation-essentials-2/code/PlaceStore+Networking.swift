import Foundation

// Adds async loading + a FileManager disk cache to the existing @Observable PlaceStore.
extension PlaceStore {

    private var cacheURL: URL {
        let dir = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
        return dir.appendingPathComponent("places.json")
    }

    /// Fetch from the network; on success update + cache; on failure fall back to cache.
    @MainActor
    func reload(using service: PlaceService = PlaceService()) async {
        do {
            let fetched = try await service.fetchPlaces()
            places = fetched
            saveCache(fetched)
        } catch {
            print("reload failed: \(error.localizedDescription) — using cache")
            if let cached = loadCache() { places = cached }
        }
    }

    func saveCache(_ places: [Place]) {
        do { try JSONEncoder().encode(places).write(to: cacheURL) }
        catch { print("cache write failed:", error) }
    }

    func loadCache() -> [Place]? {
        guard let data = try? Data(contentsOf: cacheURL) else { return nil }
        return try? JSONDecoder().decode([Place].self, from: data)
    }
}

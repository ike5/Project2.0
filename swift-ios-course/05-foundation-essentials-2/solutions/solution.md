# Challenge 05 — Reference Solution

### 1. Loading state
```swift
enum LoadState: Equatable { case idle, loading, loaded, failed(String) }

@Observable final class PlacesViewModel {
    private(set) var places: [Place] = []
    private(set) var state: LoadState = .idle
    private let service: PlaceService
    init(service: PlaceService = PlaceService()) { self.service = service }

    @MainActor func load() async {
        state = .loading
        do { places = try await service.fetchPlaces(); state = .loaded }
        catch { state = .failed(Self.message(for: error)) }
    }

    static func message(for error: Error) -> String {
        guard let urlError = error as? URLError else { return error.localizedDescription }
        switch urlError.code {
        case .notConnectedToInternet: return "You're offline."
        case .timedOut: return "The request timed out."
        default: return "Couldn't load places."
        }
    }
}
```
View:
```swift
switch vm.state {
case .loading: ProgressView("Loading…")
case .failed(let msg):
    VStack { Text(msg); Button("Retry") { Task { await vm.load() } } }
default: List(vm.places) { ... }
}
```

### 2. POST a request
```swift
func submit(_ place: Place) async throws {
    var req = URLRequest(url: URL(string: "https://jsonplaceholder.typicode.com/posts")!)
    req.httpMethod = "POST"
    req.setValue("application/json", forHTTPHeaderField: "Content-Type")
    req.httpBody = try JSONEncoder().encode(place)
    let (_, response) = try await session.data(for: req)
    guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
        throw URLError(.badServerResponse)
    }
}
```

### 3. Timeout & error mapping
```swift
let config = URLSessionConfiguration.default
config.timeoutIntervalForRequest = 10
let session = URLSession(configuration: config)
// map errors: see PlacesViewModel.message(for:) above.
```

### 4. CodingKeys
```swift
struct RemotePlace: Decodable {
    let title: String
    enum CodingKeys: String, CodingKey { case title = "name" }   // JSON "name" -> .title
}
```

### 5. Stretch
`PlacesViewModel` above already owns `state` + `service`; inject it with
`@State private var vm = PlacesViewModel()` and call `.task { await vm.load() }`. The view
renders purely from `vm.state`/`vm.places`, cleanly separating UI from loading.

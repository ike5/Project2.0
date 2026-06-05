# Challenge 05 — Robust Networking

Solution in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Loading state.** Replace the bare `ProgressView` with an explicit state enum on the
   store: `enum LoadState { case idle, loading, loaded, failed(String) }`. Drive the UI
   (spinner / error message + Retry button / list) from it.

2. **POST a request.** Add `PlaceService.submit(_ place: Place) async throws` that POSTs
   JSON to `https://jsonplaceholder.typicode.com/posts` (it echoes back). Build a
   `URLRequest` with method `POST`, `Content-Type: application/json`, and a `Codable`
   body; check the status code.

3. **Timeout & errors.** Configure a `URLSession` with a 10s timeout
   (`URLSessionConfiguration`) and map `URLError`s into user-friendly messages
   (offline vs timeout vs server). Show the message in the failed state.

4. **CodingKeys.** The remote sends `name`; rename it to `title` in a local
   `Decodable` and map via `CodingKeys`. Verify decoding still works.

5. **Stretch:** Move networking into an `@Observable PlacesViewModel` that owns the
   `LoadState` and the `PlaceService`, and have the view observe it — separating UI from
   data-loading.

## Success criteria
- [ ] The UI reflects idle/loading/loaded/failed with a working Retry.
- [ ] A POST request is built correctly and its status checked.
- [ ] Network errors map to clear messages; a timeout is configured.
- [ ] `CodingKeys` remaps a field successfully.

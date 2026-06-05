# Lab 04 — Foundation Values, Test-Driven

**You'll:** add Foundation helpers to FoundationKata and prove them with `swift test`.
⏱️ ~45 min. Pure command line — fast feedback.

---

## Part A — Baseline
```bash
cd swift-ios-course/apps/FoundationKata
swift test          # all green before you start
```

## Part B — Add a URL builder
Create `Sources/FoundationKata/URLs.swift`:
```swift
import Foundation

public enum URLs {
    /// Build a URL with query items (proper percent-encoding).
    public static func search(host: String, path: String, query: [String: String]) -> URL? {
        var comps = URLComponents()
        comps.scheme = "https"
        comps.host = host
        comps.path = path
        comps.queryItems = query.isEmpty ? nil
            : query.sorted { $0.key < $1.key }.map { URLQueryItem(name: $0.key, value: $0.value) }
        return comps.url
    }
}
```
Add a test in `Tests/FoundationKataTests/FoundationKataTests.swift`:
```swift
final class URLsTests: XCTestCase {
    func testSearchURL() {
        let url = URLs.search(host: "api.example.com", path: "/search",
                              query: ["q": "swift ui", "page": "2"])
        XCTAssertEqual(url?.absoluteString,
                       "https://api.example.com/search?page=2&q=swift%20ui")
    }
}
```
```bash
swift test --filter URLsTests
```
✅ Passes — note the space became `%20` and keys are sorted. `URLComponents` handled
encoding for you.

## Part C — Add a duration formatter
Create `Sources/FoundationKata/Durations.swift`:
```swift
import Foundation

public enum Durations {
    /// "1h 5m 3s" style from seconds.
    public static func clock(_ seconds: Int) -> String {
        let h = seconds / 3600, m = (seconds % 3600) / 60, s = seconds % 60
        var parts: [String] = []
        if h > 0 { parts.append("\(h)h") }
        if m > 0 { parts.append("\(m)m") }
        parts.append("\(s)s")
        return parts.joined(separator: " ")
    }
}
```
Test:
```swift
final class DurationsTests: XCTestCase {
    func testClock() {
        XCTAssertEqual(Durations.clock(3903), "1h 5m 3s")
        XCTAssertEqual(Durations.clock(45), "45s")
    }
}
```
```bash
swift test
```
✅ All green.

## Part D — Explore dates in the REPL
```bash
swift
```
```swift
import Foundation
let f = ISO8601DateFormatter()
let d = f.date(from: "2024-06-01T00:00:00Z")!
var cal = Calendar(identifier: .gregorian); cal.timeZone = TimeZone(identifier: "UTC")!
cal.date(byAdding: .day, value: 30, to: d)!         // 30 days later
:quit
```

## What you learned
- Build URLs safely with `URLComponents` (encoding handled).
- Format durations/numbers/dates with Foundation.
- TDD against Foundation in a fast `swift test` loop.

➡️ **[challenge.md](./challenge.md)** then [Module 05](../05-foundation-essentials-2/).

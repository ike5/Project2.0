# Module 04 — Foundation Essentials I (Values & Bridging)

**Goal:** fluency with the everyday Foundation value types — strings, dates, data,
numbers, URLs, and errors — the Objective-C-derived building blocks under every app.
⏱️ ~2 h · 🎯 Prereq: 00–03. Verifiable in **FoundationKata** (`swift test`).

---

## 1. Strings

Swift `String` is a value type with full Unicode support, bridged to `NSString`:
```swift
let s = "Hello, world"
s.uppercased(); s.hasPrefix("Hello"); s.contains("world")
s.split(separator: ",").map { $0.trimmingCharacters(in: .whitespaces) }
String(format: "%.2f", 3.14159)               // "3.14"  (NSString format heritage)
let n = Int("42")                              // String -> Int? (nil if invalid)
```
Beware: `count` is grapheme clusters; `NSString.length` is UTF-16 units — they can
differ for emoji/accents.

## 2. Dates & calendars (NSDate/NSCalendar heritage)

`Date` is just a point in time (seconds since a reference). Formatting/parsing and math
go through formatters and `Calendar`:
```swift
let now = Date()
let iso = ISO8601DateFormatter().string(from: now)        // "2024-…T…Z"
let df = DateFormatter(); df.dateStyle = .medium           // localized display
let pretty = df.string(from: now)
// modern formatting:
let s = now.formatted(date: .abbreviated, time: .shortened)
// math:
var cal = Calendar(identifier: .gregorian)
let tomorrow = cal.date(byAdding: .day, value: 1, to: now)!
let days = cal.dateComponents([.day], from: a, to: b).day
```
FoundationKata's `Dates.swift` covers ISO parsing and day math (UTC for determinism).

## 3. Data & bytes

`Data` is a bytes buffer (`NSData`):
```swift
let bytes = Data("hi".utf8)
let text = String(decoding: bytes, as: UTF8.self)
let base64 = bytes.base64EncodedString()
let url = URL(fileURLWithPath: "/tmp/x.txt")
try bytes.write(to: url); let read = try Data(contentsOf: url)
```

## 4. Numbers, NSNumber & Measurement

```swift
let boxed: NSNumber = 3.5            // Double -> NSNumber (bridging)
let d = boxed.doubleValue
let formatted = 1234.5.formatted(.number.precision(.fractionLength(2)))   // "1,234.50"
let distance = Measurement(value: 5, unit: UnitLength.kilometers)
let miles = distance.converted(to: .miles)        // unit-aware math
```

## 5. URL & URLComponents

```swift
var comps = URLComponents(string: "https://api.example.com/search")!
comps.queryItems = [URLQueryItem(name: "q", value: "swift")]
let url = comps.url!                              // https://api.example.com/search?q=swift
url.lastPathComponent; url.scheme; url.host
```
Build URLs with `URLComponents` instead of string concatenation (handles encoding).

## 6. Errors (NSError heritage)

```swift
enum LoadError: Error { case notFound, decoding(String) }
func load() throws -> Data { throw LoadError.notFound }

// Errors bridge to NSError (domain/code/userInfo):
let ns = LoadError.notFound as NSError
print(ns.domain, ns.code)
// Add user-facing messages with LocalizedError:
extension LoadError: LocalizedError {
    var errorDescription: String? { self == .notFound ? "Not found" : "Decoding failed" }
}
```

---

## Do the lab
Extend **FoundationKata** with date/number/URL helpers and test them; format values for
display. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Reference
[`apps/FoundationKata`](../apps/FoundationKata/) — `Bridging.swift`, `Dates.swift`,
`JSON.swift`.

## Key terms
`String`/`NSString` · grapheme vs UTF-16 length · `Date`/`DateFormatter`/`Calendar` ·
`ISO8601DateFormatter` · `Data` · base64 · `NSNumber`/`Measurement` · `URLComponents` ·
`Error`/`NSError`/`LocalizedError`

**Next →** [Module 05: Foundation Essentials II](../05-foundation-essentials-2/)

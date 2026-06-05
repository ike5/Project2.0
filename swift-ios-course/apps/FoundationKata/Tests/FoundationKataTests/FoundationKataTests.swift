import XCTest
@testable import FoundationKata

final class BridgingTests: XCTestCase {
    func testNSStringLength() {
        XCTAssertEqual(Bridging.nsStringLength("hello"), 5)
    }
    func testFirstWord() {
        XCTAssertEqual(Bridging.firstWordViaNSString("hello world"), "hello")
        XCTAssertEqual(Bridging.firstWordViaNSString("single"), "single")
    }
    func testIntFromNSNumber() {
        XCTAssertEqual(Bridging.intFromNSNumber(3.9), 3)   // truncates toward zero
    }
    func testRoundTrips() {
        XCTAssertTrue(Bridging.roundTrips("café"))
    }
}

final class DatesTests: XCTestCase {
    func testISORoundTrip() {
        let date = Dates.date(fromISO8601: "2024-01-15T12:00:00Z")
        XCTAssertNotNil(date)
        XCTAssertEqual(Dates.iso8601String(from: date!), "2024-01-15T12:00:00Z")
    }
    func testDaysBetween() {
        let a = Dates.date(fromISO8601: "2024-01-01T00:00:00Z")!
        let b = Dates.date(fromISO8601: "2024-01-11T00:00:00Z")!
        XCTAssertEqual(Dates.daysBetween(a, b), 10)
        XCTAssertEqual(Dates.daysBetween(b, a), -10)
    }
}

final class JSONTests: XCTestCase {
    func testEncodeSortedKeys() throws {
        let place = Place(name: "Café", latitude: 1.5, longitude: -2.5)
        let json = try JSONKata.encode(place)
        XCTAssertEqual(json, #"{"latitude":1.5,"longitude":-2.5,"name":"Café"}"#)
    }
    func testRoundTrip() throws {
        let place = Place(name: "Park", latitude: 10, longitude: 20)
        let decoded = try JSONKata.decode(try JSONKata.encode(place))
        XCTAssertEqual(decoded, place)
    }
}

final class TextStatsTests: XCTestCase {
    func testWordCount() {
        XCTAssertEqual(TextStats.wordCount("the quick brown fox"), 4)
    }
    func testFrequencies() {
        let f = TextStats.wordFrequencies("Hi hi HELLO")
        XCTAssertEqual(f["hi"], 2)
        XCTAssertEqual(f["hello"], 1)
    }
}

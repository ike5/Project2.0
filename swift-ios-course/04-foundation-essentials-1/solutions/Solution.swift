// Reference solution for Challenge 04. Add to FoundationKata Sources + Tests.
import Foundation

public enum Challenge04 {

    // 1. Relative date
    public static func relativeString(from: Date, to: Date) -> String {
        let f = RelativeDateTimeFormatter()
        f.unitsStyle = .full
        return f.localizedString(for: from, relativeTo: to)
    }

    // 2. Slugify
    public static func slug(_ text: String) -> String {
        let lowered = text.lowercased()
        let pieces = lowered.split { !$0.isLetter && !$0.isNumber }
        return pieces.joined(separator: "-")
    }

    // 3. Bytes formatter
    public static func format(bytes: Int64) -> String {
        let f = ByteCountFormatter()
        f.allowedUnits = [.useKB, .useMB, .useGB]
        f.countStyle = .file
        return f.string(fromByteCount: bytes)
    }

    // 4. Money via Decimal
    public static func parseMoney(_ s: String) -> Decimal? {
        let cleaned = s.filter { $0.isNumber || $0 == "." || $0 == "-" }
        return Decimal(string: cleaned)
    }
    public static func formatMoney(_ d: Decimal) -> String {
        let f = NumberFormatter()
        f.numberStyle = .currency
        f.locale = Locale(identifier: "en_US")
        return f.string(from: d as NSDecimalNumber) ?? "$0.00"
    }
}

/* Tests:
final class Challenge04Tests: XCTestCase {
    func testSlug() {
        XCTAssertEqual(Challenge04.slug("  Hello, World! "), "hello-world")
        XCTAssertEqual(Challenge04.slug("Swift 6 & iOS"), "swift-6-ios")
    }
    func testBytes() {
        // ByteCountFormatter output is locale-ish; assert it contains the unit:
        XCTAssertTrue(Challenge04.format(bytes: 1_500_000).contains("MB"))
    }
    func testMoney() {
        let d = Challenge04.parseMoney("$1,234.50")
        XCTAssertEqual(d, Decimal(string: "1234.50"))
    }
}
*/

// Why Decimal for money:
// Double is binary floating-point: 0.1 + 0.2 != 0.3 exactly, and rounding errors
// accumulate over many operations — unacceptable for currency. Decimal (NSDecimalNumber)
// is base-10 with exact representation of decimal fractions, so cents stay precise.

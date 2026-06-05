import Foundation

/// Date/Calendar utilities — the Foundation date stack (NSDate/NSCalendar heritage).
public enum Dates {

    /// Format a `Date` as an ISO-8601 string, e.g. "2024-01-15T12:00:00Z".
    public static func iso8601String(from date: Date) -> String {
        ISO8601DateFormatter().string(from: date)
    }

    /// Parse an ISO-8601 string into a `Date` (nil if malformed).
    public static func date(fromISO8601 s: String) -> Date? {
        ISO8601DateFormatter().date(from: s)
    }

    /// Whole calendar days from `a` to `b`, computed in UTC for determinism.
    public static func daysBetween(_ a: Date, _ b: Date) -> Int {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(identifier: "UTC")!
        let start = calendar.startOfDay(for: a)
        let end = calendar.startOfDay(for: b)
        return calendar.dateComponents([.day], from: start, to: end).day ?? 0
    }
}

import Foundation

/// Demonstrates Swift <-> Objective-C (Foundation) value bridging with robust,
/// cross-platform APIs. See cheatsheets/foundation-bridging.md.
public enum Bridging {

    /// `String` bridges to `NSString`; `.length` is the NSString (UTF-16) length.
    public static func nsStringLength(_ s: String) -> Int {
        (s as NSString).length
    }

    /// Use an NSString API (`range(of:)` + `substring(to:)`) to get the first word.
    public static func firstWordViaNSString(_ s: String) -> String {
        let ns = s as NSString
        let space = ns.range(of: " ")
        return space.location == NSNotFound ? s : ns.substring(to: space.location)
    }

    /// `Double`/`Int` bridge to `NSNumber`; `.intValue` truncates toward zero.
    public static func intFromNSNumber(_ value: Double) -> Int {
        NSNumber(value: value).intValue
    }

    /// Round-trip a Swift String up to NSString and back — bridging preserves it.
    public static func roundTrips(_ s: String) -> Bool {
        let ns: NSString = s as NSString
        let back: String = ns as String
        return back == s
    }
}

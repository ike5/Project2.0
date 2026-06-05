import Foundation

/// Small text utilities, pure Swift standard library.
public enum TextStats {

    /// Count whitespace-separated words.
    public static func wordCount(_ text: String) -> Int {
        text.split(whereSeparator: { $0 == " " || $0 == "\n" || $0 == "\t" }).count
    }

    /// Case-insensitive word frequencies, splitting on non-letters.
    public static func wordFrequencies(_ text: String) -> [String: Int] {
        var counts: [String: Int] = [:]
        for word in text.lowercased().split(whereSeparator: { !$0.isLetter }) {
            counts[String(word), default: 0] += 1
        }
        return counts
    }
}

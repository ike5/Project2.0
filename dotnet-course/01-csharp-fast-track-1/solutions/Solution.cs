// Reference solution for Challenge 01. Drop these into a console Program.cs to try.
// (Methods are written as static local/helper methods.)

using System;
using System.Collections.Generic;
using System.Linq;

public static class Challenge01
{
    // 1. The BUG: mutates the caller's list because List is a reference type.
    public static void AddTaxBuggy(List<decimal> prices)
    {
        for (int i = 0; i < prices.Count; i++)
            prices[i] *= 1.10m;            // changes the original list!
    }

    // The FIX: return a NEW list; don't touch the input.
    public static List<decimal> WithTax(IReadOnlyList<decimal> prices)
        => prices.Select(p => p * 1.10m).ToList();

    // 2. Null-safe dictionary lookup.
    public static string GetOrDefault(Dictionary<string, string> config, string key, string fallback)
        => config.TryGetValue(key, out var value) ? value : fallback;

    // 3. Classify with a switch expression.
    public static string Grade(int score) => score switch
    {
        < 0 or > 100 => "invalid",
        >= 90 => "A",
        >= 80 => "B",
        >= 70 => "C",
        _ => "F",
    };

    // 4. Null-safe first word, no '!' and no warnings.
    public static string FirstWord(string? sentence)
    {
        if (string.IsNullOrWhiteSpace(sentence))
            return "(empty)";
        // After the guard, the compiler knows 'sentence' is non-null here.
        return sentence.Split(' ', StringSplitOptions.RemoveEmptyEntries)[0];
    }

    public static void Demo()
    {
        var prices = new List<decimal> { 10m, 20m };
        var taxed = WithTax(prices);
        Console.WriteLine($"original untouched: {string.Join(",", prices)} | taxed: {string.Join(",", taxed)}");

        var cfg = new Dictionary<string, string> { ["env"] = "dev" };
        Console.WriteLine(GetOrDefault(cfg, "missing", "n/a"));   // n/a

        Console.WriteLine(Grade(95));   // A
        Console.WriteLine(Grade(150));  // invalid

        Console.WriteLine(FirstWord(null));         // (empty)
        Console.WriteLine(FirstWord("  hello world"));  // hello
    }
}

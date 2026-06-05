namespace ConsolePlayground.Demos;

/// <summary>Module 01: the type system, value vs reference, nullability.</summary>
public static class TypesDemo
{
    public static void Run()
    {
        // Value types are copied on assignment.
        int a = 10;
        int b = a;          // copy
        b = 99;
        Console.WriteLine($"value types: a={a}, b={b} (a unchanged)");

        // Reference types share the same underlying object.
        var list1 = new List<int> { 1, 2, 3 };
        var list2 = list1;  // same reference
        list2.Add(4);
        Console.WriteLine($"reference types: list1.Count={list1.Count} (sees the Add)");

        // Nullable reference types: the compiler tracks possible nulls.
        string? maybeName = MaybeGet(false);
        // Safe access patterns:
        int length = maybeName?.Length ?? 0;             // null-conditional + null-coalescing
        Console.WriteLine($"nullable: name='{maybeName ?? "<null>"}', safe length={length}");

        // Parsing safely (no exceptions on bad input):
        Console.WriteLine(int.TryParse("123", out var n) ? $"parsed {n}" : "parse failed");
        Console.WriteLine(int.TryParse("oops", out _) ? "parsed" : "parse failed (as expected)");

        // String interpolation & formatting.
        decimal price = 19.5m;
        Console.WriteLine($"formatted: {price:C} at {DateTime.Now:yyyy-MM-dd}");
    }

    private static string? MaybeGet(bool present) => present ? "Ada" : null;
}

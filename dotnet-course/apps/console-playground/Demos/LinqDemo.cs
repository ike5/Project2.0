namespace ConsolePlayground.Demos;

/// <summary>Module 03: generics, LINQ, delegates/lambdas, pattern matching.</summary>
public static class LinqDemo
{
    private record Employee(string Name, string Dept, int Salary);

    public static void Run()
    {
        var staff = new List<Employee>
        {
            new("Ada", "Eng", 120),
            new("Linus", "Eng", 110),
            new("Grace", "Ops", 95),
            new("Edsger", "Eng", 130),
            new("Margaret", "Ops", 100),
        };

        // LINQ: filter -> project -> order.
        var topEng = staff
            .Where(e => e.Dept == "Eng")
            .OrderByDescending(e => e.Salary)
            .Select(e => e.Name)
            .ToList();
        Console.WriteLine($"Eng by salary: {string.Join(", ", topEng)}");

        // Grouping & aggregation.
        var avgByDept = staff
            .GroupBy(e => e.Dept)
            .Select(g => new { Dept = g.Key, Avg = g.Average(e => e.Salary) });
        foreach (var row in avgByDept)
            Console.WriteLine($"  {row.Dept}: avg {row.Avg:0.0}");

        // Delegates & lambdas as first-class values.
        Func<Employee, bool> isWellPaid = e => e.Salary >= 110;
        Console.WriteLine($"well paid: {staff.Count(isWellPaid)}");

        // A generic helper method.
        Console.WriteLine($"highest paid: {MaxBySelector(staff, e => e.Salary).Name}");

        // Pattern matching.
        foreach (var e in staff.Take(2))
            Console.WriteLine($"  {e.Name} -> {Classify(e.Salary)}");
    }

    // Generic method with a constraint.
    private static T MaxBySelector<T>(IEnumerable<T> items, Func<T, int> selector)
        => items.OrderByDescending(selector).First();

    private static string Classify(int salary) => salary switch
    {
        < 100 => "entry",
        >= 100 and < 125 => "mid",
        _ => "senior",
    };
}

// Top-level statements: this file is the program entry point (no Main boilerplate).
// A tiny menu that runs the fundamentals demos. Used across Modules 01-04.
using ConsolePlayground.Demos;

var demos = new (string Name, Func<Task> Run)[]
{
    ("Types & nullability (Module 01)", () => Task.Run(TypesDemo.Run)),
    ("OOP: classes, records, interfaces (Module 02)", () => Task.Run(OopDemo.Run)),
    ("Generics, LINQ, delegates (Module 03)", () => Task.Run(LinqDemo.Run)),
    ("Async/await (Module 04)", AsyncDemo.RunAsync),
};

// If an arg is passed (e.g. `dotnet run -- 3`), run that demo directly; else show a menu.
int? choice = args.Length > 0 && int.TryParse(args[0], out var a) ? a : null;

if (choice is null)
{
    Console.WriteLine("=== .NET Console Playground ===");
    for (int i = 0; i < demos.Length; i++)
        Console.WriteLine($"  {i + 1}. {demos[i].Name}");
    Console.Write("Pick a demo (1-4), or 'a' for all: ");
    var input = Console.ReadLine()?.Trim();
    if (input is "a" or "A")
    {
        foreach (var demo in demos) { await RunOne(demo); }
        return;
    }
    choice = int.TryParse(input, out var c) ? c : 1;
}

var index = Math.Clamp(choice.Value, 1, demos.Length) - 1;
await RunOne(demos[index]);

static async Task RunOne((string Name, Func<Task> Run) demo)
{
    Console.WriteLine();
    Console.WriteLine($"--- {demo.Name} ---");
    await demo.Run();
}

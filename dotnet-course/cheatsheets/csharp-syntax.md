# C# Syntax Cheatsheet (for an experienced dev)

A fast reference mapping things you already know to C#. C# 12 / .NET 8.

## Program entry — top-level statements
Since C# 9 a console app can skip the `Main` boilerplate:
```csharp
// Program.cs — this IS the entry point
Console.WriteLine("Hello");
int sum = Add(2, 3);
int Add(int a, int b) => a + b;     // local function
```
The classic form still exists:
```csharp
namespace MyApp;
class Program { static void Main(string[] args) { /* ... */ } }
```

## Variables & types
```csharp
int n = 42;            // value type
double d = 3.14;
bool ok = true;
char c = 'x';
string s = "text";     // reference type, immutable
var inferred = "auto"; // type inferred (still static!)
const int Max = 100;
decimal money = 9.99m; // for currency
```
Nullable:
```csharp
int? maybe = null;          // nullable value type
string? name = null;        // nullable reference type (NRT)
string sure = name!;        // null-forgiving (you assert non-null)
int len = name?.Length ?? 0;// null-conditional + null-coalescing
```

## Collections
```csharp
int[] arr = [1, 2, 3];                 // collection expression (C# 12)
var list = new List<string> { "a" };
var map  = new Dictionary<string,int> { ["x"] = 1 };
var set  = new HashSet<int> { 1, 2 };
(string, int) tuple = ("a", 1);        // value tuple
```

## Control flow
```csharp
if (n > 0) { } else if (n < 0) { } else { }
for (int i = 0; i < 10; i++) { }
foreach (var item in list) { }
while (ok) { }  do { } while (ok);

string label = n switch {               // switch expression
    < 0      => "neg",
    0        => "zero",
    > 0 and < 10 => "small",
    _        => "big",
};
```

## Methods
```csharp
int Square(int x) => x * x;             // expression-bodied
void Log(string msg, int level = 1) {}  // optional param
int Sum(params int[] nums) => nums.Sum();
bool TryGet(string key, out int value) { value = 0; return false; } // out param
```

## Classes, records, structs
```csharp
public class Account {
    public string Owner { get; init; } = "";   // init-only
    public decimal Balance { get; private set; }
    public Account(string owner) => Owner = owner;
    public void Deposit(decimal amt) => Balance += amt;
}

public record Money(string Currency, decimal Amount);   // immutable + value equality
public readonly struct Point(int X, int Y);             // value type
public enum Status { Active, Closed }
```

## Interfaces & inheritance
```csharp
public interface IGreeter { string Greet(string name); }
public class Greeter : IGreeter {
    public string Greet(string name) => $"Hi {name}";   // string interpolation
}
public abstract class Shape { public abstract double Area(); }
public class Circle(double r) : Shape {                 // primary constructor (C# 12)
    public override double Area() => Math.PI * r * r;
}
```

## Generics
```csharp
T First<T>(IEnumerable<T> xs) => xs.First();
public class Box<T> { public T? Value { get; set; } }
void Constrained<T>(T x) where T : class, IComparable<T> { }
```

## Delegates, lambdas, events
```csharp
Func<int,int> dbl = x => x * 2;         // returns a value
Action<string> log = msg => Console.WriteLine(msg);  // returns void
Predicate<int> isEven = x => x % 2 == 0;

public event EventHandler? Changed;     // declare
Changed?.Invoke(this, EventArgs.Empty); // raise
```

## Exceptions
```csharp
try { Risky(); }
catch (IOException ex) when (ex.Message.Contains("disk")) { /* filtered */ }
catch (Exception ex) { Console.Error.WriteLine(ex); throw; }
finally { /* always runs */ }
```

## Resource cleanup
```csharp
using var stream = File.OpenRead("f.txt");   // disposed at end of scope
using (var conn = Open()) { /* ... */ }       // disposed at end of block
```

## Async
```csharp
async Task<string> FetchAsync(HttpClient http, string url) {
    var resp = await http.GetStringAsync(url);
    return resp.Trim();
}
await Task.WhenAll(t1, t2);
```

## Useful idioms
```csharp
var full = $"{first} {last}";                 // interpolation
var text = """
    raw "multi-line"
    string literal
    """;                                       // raw string literal
obj is Account { Balance: > 0 } a;             // property pattern -> binds 'a'
list.ForEach(Console.WriteLine);               // method group
```

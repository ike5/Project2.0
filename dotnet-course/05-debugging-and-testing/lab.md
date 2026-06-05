# Lab 05 — Debug, Then Test the Fix

**You'll:** use the debugger to find a bug, then apply reproduce → failing test → fix.
⏱️ ~50 min.

---

## Part A — Set up a project with the buggy code
```bash
mkdir -p ~/dev/lab05 && cd ~/dev/lab05
dotnet new console -n Lab05 && cd Lab05
# copy the buggy class in:
cp <repo>/dotnet-course/05-debugging-and-testing/code/BuggyInventory.cs .
```
Replace `Program.cs`:
```csharp
using Lab05;

var inv = new Inventory();
inv.Add(new Item("widget", 10m, 3));
inv.Add(new Item("gadget", 20m, 0));   // zero quantity on purpose

Console.WriteLine($"avg price: {inv.AveragePrice()}");
Console.WriteLine($"total value: {inv.TotalValue()}");

var empty = new Inventory();
Console.WriteLine($"empty avg: {empty.AveragePrice()}");   // will throw
```
```bash
dotnet run
```
✅ It throws `System.InvalidOperationException: Sequence contains no elements` on the
empty inventory. Read the stack trace — note the method + line.

## Part B — Debug it
1. Open the folder in VS Code (`code .`). Ensure the **C# Dev Kit** is installed.
2. Set a **breakpoint** on the `Console.WriteLine($"total value...")` line.
3. Press `F5` to start debugging. When it pauses, hover over `inv` / open **Locals**
   and expand `_items` — confirm the two items.
4. **Step into** (`F11`) `TotalValue()`. Watch it compute `_items.Count * _items.First().Price`
   = `2 * 10` = `20` — but the *correct* total is `10*3 + 20*0 = 30`. You've found Bug 2.
5. Add an **exception breakpoint** (Run → Breakpoints → "All Exceptions" / "User-Unhandled")
   and continue; it breaks exactly where `AveragePrice()` throws on the empty list (Bug 1).

✅ You located both bugs by inspection and by breaking on the throw — no guessing.

## Part C — Reproduce with a failing test
```bash
cd ~/dev/lab05
dotnet new xunit -n Lab05.Tests
dotnet add Lab05.Tests/Lab05.Tests.csproj reference Lab05/Lab05.csproj
```
Add `Lab05.Tests/InventoryTests.cs`:
```csharp
using Lab05;
using Xunit;

public class InventoryTests
{
    [Fact]
    public void TotalValue_sums_price_times_quantity()
    {
        var inv = new Inventory();
        inv.Add(new Item("widget", 10m, 3));
        inv.Add(new Item("gadget", 20m, 0));
        Assert.Equal(30m, inv.TotalValue());   // FAILS against the buggy code
    }

    [Fact]
    public void AveragePrice_on_empty_is_zero_not_throw()
    {
        Assert.Equal(0m, new Inventory().AveragePrice());   // FAILS (throws) today
    }
}
```
```bash
dotnet test
```
✅ Both tests **fail** — you've reproduced the bugs as executable specs.

## Part D — Fix until green
Edit `BuggyInventory.cs`:
```csharp
public decimal AveragePrice() => _items.Count == 0 ? 0m : _items.Average(i => i.Price);
public decimal TotalValue() => _items.Sum(i => i.Price * i.Quantity);
```
```bash
dotnet test        # now: Passed!
dotnet run         # empty avg prints 0; total value prints 30
```
✅ Tests pass and the regression is locked in. (Reference fix in [`solutions/`](./solutions/).)

## Part E — Run the real suite
```bash
cd <repo>/dotnet-course/apps/TaskApi
dotnet test
```
✅ The TaskApi xUnit suite passes. Open `tests/TaskApi.Tests/TaskServiceTests.cs` and
read how it uses the EF Core **InMemory** provider to isolate `TaskService`.

## What you learned
- Read a stack trace to the first line of your code.
- Drive breakpoints, stepping, Locals, and exception breakpoints.
- Reproduce a bug as a failing xUnit test, then fix to green.

➡️ **[challenge.md](./challenge.md)** then [Module 06](../06-logging-config-diagnostics/).

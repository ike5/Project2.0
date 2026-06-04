// Reference solution for Challenge 04 (tasks 2-4). Task 1 is CLI:
//   dotnet new sln -n Bank
//   dotnet new classlib -n Bank.Core
//   dotnet new console  -n Bank.App
//   dotnet new xunit    -n Bank.Tests
//   dotnet sln add **/*.csproj
//   dotnet add Bank.App/Bank.App.csproj   reference Bank.Core/Bank.Core.csproj
//   dotnet add Bank.Tests/Bank.Tests.csproj reference Bank.Core/Bank.Core.csproj
//   dotnet test

using System;
using System.Diagnostics;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

public static class Challenge04
{
    // 2. Concurrent fan-out
    public static async Task<int[]> DownloadAllAsync(string[] urls, CancellationToken ct = default)
    {
        // Start ALL tasks first, then await them together -> they overlap.
        var tasks = urls.Select(u => DownloadOneAsync(u, ct));
        return await Task.WhenAll(tasks);
    }

    private static async Task<int> DownloadOneAsync(string url, CancellationToken ct)
    {
        int ms = 50 + url.Length * 10;             // fake latency derived from the url
        await Task.Delay(ms, ct);                  // 4. honors cancellation
        return ms;                                  // pretend: bytes downloaded
    }

    // 3. Why .Result is dangerous (and the async fix)
    // BAD:  var sizes = DownloadAllAsync(urls).Result;
    //   -> blocks the calling thread; in apps with a SynchronizationContext this can
    //      DEADLOCK, and under load it starves the thread pool. Never block on async.
    // GOOD: make the whole call chain async and 'await' it (see RunAsync below).

    public static async Task RunAsync()
    {
        string[] urls = ["https://a", "https://bbb", "https://cccccc"];

        var sw = Stopwatch.StartNew();
        int total = 0;
        foreach (var u in urls) total += await DownloadOneAsync(u, default);   // sequential
        Console.WriteLine($"sequential: {sw.ElapsedMilliseconds}ms, total={total}");

        sw.Restart();
        var sizes = await DownloadAllAsync(urls);                               // concurrent
        Console.WriteLine($"concurrent: {sw.ElapsedMilliseconds}ms, total={sizes.Sum()}");

        // 4. Cancellation demo
        using var cts = new CancellationTokenSource(100);
        try
        {
            await DownloadAllAsync(["https://slowwwwwwwwwww"], cts.Token);
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("cancelled as expected");
        }
    }
}

namespace ConsolePlayground.Demos;

/// <summary>Module 04: async/await and Tasks.</summary>
public static class AsyncDemo
{
    public static async Task RunAsync()
    {
        Console.WriteLine("starting two 'downloads' concurrently...");

        var sw = System.Diagnostics.Stopwatch.StartNew();

        // Start both tasks, THEN await them together -> they overlap.
        Task<int> a = FakeDownloadAsync("a", 300);
        Task<int> b = FakeDownloadAsync("b", 400);

        int[] sizes = await Task.WhenAll(a, b);

        sw.Stop();
        Console.WriteLine($"both done in ~{sw.ElapsedMilliseconds} ms " +
                          $"(concurrent, not 700) sizes=[{string.Join(", ", sizes)}]");

        // Demonstrating sequential await for contrast.
        int total = await SumSequentialAsync();
        Console.WriteLine($"sequential total = {total}");
    }

    private static async Task<int> FakeDownloadAsync(string name, int ms)
    {
        await Task.Delay(ms);                 // non-blocking wait
        Console.WriteLine($"  '{name}' finished after {ms} ms");
        return ms;                            // pretend this is bytes downloaded
    }

    private static async Task<int> SumSequentialAsync()
    {
        int sum = 0;
        foreach (var ms in new[] { 50, 60 })
            sum += await FakeDownloadAsync("seq", ms);
        return sum;
    }
}

// Reference solution for Challenge 03.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;

public record LogEntry(DateTime Time, string Level, string Message);

// 2. Generic Result<T>
public readonly struct Result<T>
{
    public bool IsSuccess { get; }
    public T? Value { get; }
    public string? Error { get; }

    private Result(bool ok, T? value, string? error) { IsSuccess = ok; Value = value; Error = error; }

    public static Result<T> Ok(T value) => new(true, value, null);
    public static Result<T> Fail(string error) => new(false, default, error);
}

public static class Challenge03
{
    // 1. LINQ report
    public static void Report(List<LogEntry> logs)
    {
        var perLevel = logs
            .GroupBy(l => l.Level)
            .Select(g => new { Level = g.Key, Count = g.Count() })
            .OrderByDescending(x => x.Count);
        foreach (var row in perLevel) Console.WriteLine($"{row.Level}: {row.Count}");

        var recentErrors = logs
            .Where(l => l.Level == "Error")
            .OrderByDescending(l => l.Time)
            .Take(3)
            .Select(l => l.Message)
            .ToList();
        Console.WriteLine("recent errors: " + string.Join(" | ", recentErrors));

        bool errorLastHour = logs.Any(l => l.Level == "Error" && l.Time >= DateTime.Now.AddHours(-1));
        Console.WriteLine($"error in last hour: {errorLastHour}");
    }

    // 2. Parse without exceptions
    public static Result<int> ParseAge(string s)
        => int.TryParse(s, out var age) && age >= 0
            ? Result<int>.Ok(age)
            : Result<int>.Fail($"'{s}' is not a valid age");

    // 3. Retry preserving the final stack trace
    public static T Retry<T>(Func<T> action, int times)
    {
        for (int attempt = 1; ; attempt++)
        {
            try { return action(); }
            catch when (attempt < times) { /* swallow and retry */ }
            // on the last attempt, no filter matches -> the exception propagates naturally
        }
    }

    public static void Demo()
    {
        Console.WriteLine(ParseAge("30").IsSuccess);   // True
        Console.WriteLine(ParseAge("x").Error);        // 'x' is not a valid age

        int attempts = 0;
        int value = Retry(() => { attempts++; if (attempts < 3) throw new InvalidOperationException("flaky"); return 42; }, 5);
        Console.WriteLine($"got {value} after {attempts} attempts");

        using (new Timer()) { System.Threading.Thread.Sleep(20); }
    }
}

// 4. Disposable timer
public sealed class Timer : IDisposable
{
    private readonly Stopwatch _sw = Stopwatch.StartNew();
    public void Dispose()
    {
        _sw.Stop();
        Console.WriteLine($"elapsed: {_sw.ElapsedMilliseconds} ms");
    }
}

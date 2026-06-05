# Module 06 — Logging, Configuration & Diagnostics

**Goal:** the things you live in during app support — **structured logs** you can
search, **configuration** that changes per environment, and **secrets** kept out of
code. ⏱️ ~2 h · 🎯 Prereq: 00–05.

---

## 1. Logging with `ILogger`

.NET has a built-in logging abstraction. You inject `ILogger<T>` and call level
methods:
```csharp
public class TaskService(ILogger<TaskService> logger)
{
    public void Complete(int id)
    {
        logger.LogInformation("Completing task {TaskId}", id);   // structured!
        try { /* ... */ }
        catch (Exception ex)
        {
            logger.LogError(ex, "Failed to complete task {TaskId}", id);
            throw;
        }
    }
}
```

### Structured logging (the key idea)
Use **message templates with named placeholders**, not string interpolation:
```csharp
logger.LogInformation("Completing task {TaskId}", id);   // ✅ TaskId is a searchable field
logger.LogInformation($"Completing task {id}");          // ❌ just flat text, not queryable
```
A structured backend (Serilog → Seq/Elasticsearch/console JSON) records `TaskId` as a
field you can **filter and aggregate** on ("show all logs where TaskId=42"). This is
what makes production logs *useful* instead of noise.

### Levels
`Trace < Debug < Information < Warning < Error < Critical`. Configure the **minimum**
level per environment (verbose in dev, Information+ in prod). Always pass the
**exception object** to `LogError(ex, ...)` so the stack trace is captured.

### Serilog
The TaskApi uses **Serilog** (`Serilog.AspNetCore`), configured from `appsettings.json`,
plus `app.UseSerilogRequestLogging()` to log each HTTP request as one structured line.

## 2. Configuration

ASP.NET Core builds configuration from layered sources (later overrides earlier):
```
appsettings.json  →  appsettings.{Environment}.json  →  env vars  →  user-secrets  →  CLI args
```
Read values:
```csharp
var conn = builder.Configuration.GetConnectionString("Default");
var flag = builder.Configuration.GetValue<bool>("Features:NewUi");
```
The **environment** comes from `ASPNETCORE_ENVIRONMENT` (`Development`/`Production`).
`appsettings.Development.json` only applies in Development — that's how you get
verbose logs locally but not in prod.

### The Options pattern (typed config)
Bind a config section to a class and inject it:
```csharp
public class EmailOptions { public string From { get; set; } = ""; public int Retries { get; set; } }

builder.Services.Configure<EmailOptions>(builder.Configuration.GetSection("Email"));

public class Mailer(IOptions<EmailOptions> options)
{
    private readonly EmailOptions _opts = options.Value;   // strongly typed
}
```
Prefer typed Options over scattering magic strings through the code.

## 3. Secrets (never commit them)

Connection strings with passwords, API keys — keep them out of `appsettings.json`:
- **Local dev:** the **user-secrets** tool stores them outside the repo:
  ```bash
  dotnet user-secrets init
  dotnet user-secrets set "Email:ApiKey" "sk-local-123"
  ```
  They layer into configuration automatically in Development.
- **Production:** environment variables or a secret manager (Azure Key Vault, AWS
  Secrets Manager). Env var names map with `__` (double underscore) for nesting:
  `Email__ApiKey=...` → `Email:ApiKey`.

## 4. Diagnostics tools (know they exist)

For live processes: `dotnet-counters` (CPU/GC/req-rate), `dotnet-trace` (sampling
profiler), `dotnet-dump` (memory dumps). Install as global tools; invaluable for
"the app is slow/hung in prod" tickets.

---

## Do the lab
Add structured logging + typed Options + a user-secret to the TaskApi, change
behavior by environment, and read logs to trace a request. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
`ILogger<T>` · message template · structured logging · log levels · Serilog ·
`IConfiguration` · layered config · environments · Options pattern · `IOptions<T>` ·
user-secrets · env var `__` nesting · dotnet-counters/trace/dump

**Next →** [Module 07: Web APIs with ASP.NET Core](../07-web-apis-aspnet-core/)

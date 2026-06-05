# Lab 06 — Logs, Config & Secrets on TaskApi

**You'll:** make TaskApi's logs structured and searchable, add typed Options, change
behavior by environment, and store a secret safely. ⏱️ ~50 min.

> Work in a **copy** of the reference app so you can experiment freely:
> ```bash
> cp -r <repo>/dotnet-course/apps/TaskApi ~/dev/TaskApi && cd ~/dev/TaskApi/src/TaskApi
> ```

---

## Part A — See structured logging
```bash
dotnet run
# in another terminal:
curl -s -X POST http://localhost:5080/api/tasks -H 'Content-Type: application/json' -d '{"title":"log me"}' >/dev/null
curl -s http://localhost:5080/api/tasks >/dev/null
```
✅ In the app's console you'll see Serilog lines including the request log and
`Created task {TaskId} {Title}` with the **values filled in**. Stop with `Ctrl+C`.

## Part B — Add a searchable field with a scope
Open `Services/TaskService.cs`. The `CreateAsync` already logs
`"Created task {TaskId} {Title}"`. Add a correlation scope around the work:
```csharp
using (logger.BeginScope("op:{Operation}", "CreateTask"))
{
    logger.LogInformation("Created task {TaskId} {Title}", item.Id, item.Title);
}
```
Run again and create a task — the `Operation` field now rides along on those logs.
✅ This is how you correlate all logs for one operation in a real log store.

## Part C — Change behavior by environment
`appsettings.Development.json` sets Serilog to `Debug`. Prove environment switching:
```bash
ASPNETCORE_ENVIRONMENT=Development dotnet run    # Debug-level logs, Swagger enabled
# stop, then:
ASPNETCORE_ENVIRONMENT=Production  dotnet run     # Information+ only, no Swagger
```
✅ Same binary, different config, because `appsettings.{Environment}.json` and the
`IsDevelopment()` checks in `Program.cs` react to the environment.

## Part D — Typed Options
Add `Options/ApiOptions.cs`:
```csharp
namespace TaskApi.Options;
public class ApiOptions
{
    public int MaxTitleLength { get; set; } = 200;
    public string Owner { get; set; } = "unknown";
}
```
Add to `appsettings.json`:
```json
"Api": { "MaxTitleLength": 50, "Owner": "support-team" }
```
Register and use it in `Program.cs`:
```csharp
builder.Services.Configure<TaskApi.Options.ApiOptions>(builder.Configuration.GetSection("Api"));
```
Expose it to verify binding — add an endpoint:
```csharp
app.MapGet("/api/info", (Microsoft.Extensions.Options.IOptions<TaskApi.Options.ApiOptions> opts) =>
    Results.Ok(opts.Value));
```
```bash
dotnet run
curl -s http://localhost:5080/api/info ; echo     # {"maxTitleLength":50,"owner":"support-team"}
```
✅ Config bound into a typed object, injected via `IOptions<T>`.

## Part E — A secret (kept out of the repo)
```bash
dotnet user-secrets init
dotnet user-secrets set "Api:ApiKey" "sk-local-do-not-commit"
```
Add `ApiKey` to `ApiOptions`, then log only that it's present (never the value):
```csharp
// in Program.cs after building config, for the demo:
var hasKey = !string.IsNullOrEmpty(builder.Configuration["Api:ApiKey"]);
Console.WriteLine($"API key configured: {hasKey}");
```
```bash
dotnet run        # prints: API key configured: True
```
✅ The secret lives in your user profile, not `appsettings.json` — `git status` shows
nothing to commit. In prod you'd supply it via `Api__ApiKey` env var or a vault.

## What you learned
- Structured logs record searchable fields (and scopes correlate operations).
- Layered configuration + environments change behavior without rebuilding.
- The Options pattern binds config to typed classes.
- user-secrets keep credentials out of source control.

➡️ **[challenge.md](./challenge.md)** then [Module 07](../07-web-apis-aspnet-core/).

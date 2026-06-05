# Lab/Challenge 09 — Reference Solution

## The four planted bugs

### Bug 1 — Configuration (`Defualt` typo)
- **Symptom:** data "missing"; app uses the fallback DB.
- **Evidence:** `GetConnectionString("Default")` returns null → code falls back to
  `"Data Source=tasks.db"` but the intended key was misspelled, so a different/empty DB
  is used.
- **Fix:** correct the key to `"Default"`. **Guard:** log the resolved path at startup
  (`logger.LogInformation("Using DB {Path}", connectionString)`), and consider throwing
  if the key is missing in Production.

### Bug 2 — Unhandled exception → 500
- **Symptom:** `GET /api/tasks/9999` returns 500.
- **Evidence:** `NullReferenceException` at `TaskService.GetAsync` — `FindAsync`
  returned null and `ToDto(item!)` dereferenced it.
- **Fix:** `return item is null ? null : ToDto(item);` (endpoint maps null → 404).
- **Test:** `GetAsync(unknownId)` returns null.

### Bug 3 — Translation error → 500
- **Symptom:** `GET /api/tasks` returns 500; log: `... could not be translated`.
- **Evidence:** `.Select(t => ToDto(t)).ToListAsync()` asks EF to translate a private
  C# method into SQL.
- **Fix:** materialize first, then map:
  ```csharp
  var items = await db.Tasks.OrderBy(t => t.Id).ToListAsync();
  return items.Select(ToDto).ToList();
  ```
- **Test:** `GetAllAsync` after a create returns the row (EF InMemory hides this; a
  SQLite-backed integration test catches translation issues).

### Bug 4 — DI lifetime mismatch
- **Symptom:** `Cannot consume scoped service 'TaskDbContext' from singleton
  'ITaskService'` at startup/first request.
- **Evidence:** `AddSingleton<ITaskService, TaskService>()` — a singleton can't depend
  on a scoped `DbContext` (the DbContext is per-request).
- **Fix:** `AddScoped<ITaskService, TaskService>()`.

---

## Challenge answers

### 1. Multi-stage Dockerfile
```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY . .
RUN dotnet publish src/TaskApi/TaskApi.csproj -c Release -o /app

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /app .
EXPOSE 8080
ENV ASPNETCORE_URLS=http://+:8080
ENTRYPOINT ["dotnet", "TaskApi.dll"]
```
> Stage 1 (SDK image) **builds/publishes**; stage 2 (smaller aspnet runtime image)
> **runs** only the published output — smaller, fewer tools, smaller attack surface.

### 2. Graceful config + startup log
```csharp
var connectionString = builder.Configuration.GetConnectionString("Default")
    ?? "Data Source=tasks.db";
// after build:
app.Logger.LogInformation("Using database {ConnectionString}", connectionString);
```

### 4. Readiness vs liveness
> **Liveness** = "is the process running / not deadlocked?" — restart if it fails.
> **Readiness** = "can it serve requests right now / are dependencies (DB) reachable?"
> — remove from the load balancer if it fails, but don't necessarily restart.
> `AddDbContextCheck` contributes to **readiness** (it verifies the database
> dependency).

# Lab 09 — Publish, Health-Check & Diagnose

**You'll:** publish and run TaskApi, add a real health check, then diagnose four
planted production bugs. ⏱️ ~70 min.

---

## Part A — Publish and run a deployable build
```bash
cd <repo>/dotnet-course/apps/TaskApi
dotnet publish src/TaskApi/TaskApi.csproj -c Release -o ./publish
dotnet ./publish/TaskApi.dll &
sleep 2
curl -s http://localhost:5080/health ; echo        # Healthy
curl -s http://localhost:5080/api/tasks ; echo
kill %1
```
✅ A `Release` build runs from `publish/`. Try a self-contained build too:
```bash
dotnet publish src/TaskApi/TaskApi.csproj -c Release -r osx-arm64 --self-contained -o ./publish-sc
./publish-sc/TaskApi &        # native executable, no runtime needed
sleep 2; curl -s http://localhost:5080/health; echo; kill %1
```

## Part B — A meaningful health check
Add a DB health check so `/health` reflects the database, not just the process. In a
copy of the app:
```bash
dotnet add src/TaskApi/TaskApi.csproj package Microsoft.Extensions.Diagnostics.HealthChecks.EntityFrameworkCore --version 8.0.7
```
```csharp
builder.Services.AddHealthChecks()
    .AddDbContextCheck<TaskDbContext>("database");
```
```bash
dotnet run --project src/TaskApi
curl -s http://localhost:5080/health ; echo        # Healthy (now includes the DB check)
```
✅ Break it on purpose: point the connection string at an unwritable path and watch
`/health` report `Unhealthy`. That's what an orchestrator would act on.

## Part C — Diagnose the broken app
Set up the buggy copy and introduce the bugs from
[`code/broken-bugs.md`](./code/broken-bugs.md):
```bash
cp -r <repo>/dotnet-course/apps/TaskApi ~/dev/TaskApi-broken
cd ~/dev/TaskApi-broken/src/TaskApi
# apply ONE bug at a time, diagnose, fix, then the next.
```

For **each** bug, follow the support loop:
1. **Reproduce** the symptom with `curl` (or by starting the app).
2. **Read the logs / stack trace** — identify exception type + first own-code frame.
3. **Form a hypothesis**, confirm by reading the code.
4. **Fix**, and where sensible **add a test** that would have caught it.

### Bug 2 walkthrough (example)
```bash
dotnet run &
sleep 2
curl -s -i http://localhost:5080/api/tasks/9999 | head -1   # HTTP/1.1 500  (should be 404)
```
Read the app console: `NullReferenceException ... at TaskService.GetAsync ... line N`.
Hypothesis: `FindAsync` returned null and we dereferenced it. Fix:
```csharp
return item is null ? null : ToDto(item);
```
Re-run → `404`. Add a test: `GetAsync(unknownId)` returns null. ✅

Work the other three the same way. Compare with
[`solutions/solution.md`](./solutions/solution.md) **after** you've tried.

## Part D — Capstone A checkpoint
Run through the [capstone rubric](./solutions/RUBRIC.md) against your TaskApi: tests
green, migration applied, structured logs, `/health` meaningful, a published artifact,
and you can explain all four diagnoses.

## What you learned
- Publish framework-dependent vs self-contained; run the artifact.
- Health checks that reflect real dependencies.
- A repeatable production-diagnosis loop applied to four classic failures.

➡️ **[challenge.md](./challenge.md)** then [Module 10](../10-unity-setup-and-editor/).

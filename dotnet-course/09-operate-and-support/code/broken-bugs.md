# Planted Bugs for Lab 09

Apply these four bugs to a **copy** of the reference TaskApi, then diagnose them one at
a time (see `lab.md`). Each mimics a real production ticket. Reference diagnoses are in
[`../solutions/solution.md`](../solutions/solution.md).

```bash
cp -r <repo>/dotnet-course/apps/TaskApi ~/dev/TaskApi-broken
cd ~/dev/TaskApi-broken/src/TaskApi
```

---

## Bug 1 — Configuration
In `appsettings.json`, change the connection string key so the app can't find it:
```jsonc
"ConnectionStrings": { "Defualt": "Data Source=tasks.db" }   // typo: Defualt
```
**Symptom to observe:** the app falls back to a default/unexpected DB (or behaves as if
empty). Ticket: "tasks I created yesterday are gone."

## Bug 2 — Unhandled exception (500)
In `Services/TaskService.cs`, make `GetAsync` throw on a missing id instead of
returning null:
```csharp
public async Task<TaskDto?> GetAsync(int id)
{
    var item = await db.Tasks.FindAsync(id);
    return ToDto(item!);     // BUG: item may be null -> NullReferenceException -> 500
}
```
**Symptom:** `GET /api/tasks/9999` returns **500** instead of **404**. Ticket: "the app
crashes when I open a task that doesn't exist."

## Bug 3 — Data / translation
In `GetAllAsync`, project through the private method *before* materializing:
```csharp
public async Task<IReadOnlyList<TaskDto>> GetAllAsync()
    => await db.Tasks.Select(t => ToDto(t)).ToListAsync();   // BUG: not translatable
```
**Symptom:** `GET /api/tasks` returns **500**; logs show
`could not be translated`. Ticket: "the task list page is broken."

## Bug 4 — Dependency injection
In `Program.cs`, register the service with the wrong lifetime relative to the DbContext:
```csharp
builder.Services.AddSingleton<ITaskService, TaskService>();  // BUG: Singleton consuming a Scoped DbContext
```
**Symptom:** startup or first-request error:
`Cannot consume scoped service 'TaskDbContext' from singleton 'ITaskService'`.
Ticket: "the app won't start / 500 on every request after deploy."

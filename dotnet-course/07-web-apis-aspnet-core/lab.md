# Lab 07 — Build TaskApi's HTTP Layer

**You'll:** scaffold a Web API, wire DI, and implement task endpoints with model
binding and proper status codes — using an **in-memory store** (the database comes in
Module 08). ⏱️ ~55 min.

---

## Part A — Scaffold
```bash
mkdir -p ~/dev/taskapi-lab && cd ~/dev/taskapi-lab
dotnet new web -n TaskApi && cd TaskApi
dotnet run        # note the http://localhost:5xxx port, then Ctrl+C
```

## Part B — Domain + an in-memory service
Add `Models.cs`:
```csharp
namespace TaskApi;
public record CreateTaskDto(string Title);
public record TaskDto(int Id, string Title, bool IsDone);

public interface ITaskService
{
    IReadOnlyList<TaskDto> GetAll();
    TaskDto? Get(int id);
    TaskDto Create(CreateTaskDto dto);
    bool Complete(int id);
}

public class InMemoryTaskService : ITaskService
{
    private readonly List<TaskDto> _tasks = new();
    private int _nextId = 1;

    public IReadOnlyList<TaskDto> GetAll() => _tasks;
    public TaskDto? Get(int id) => _tasks.FirstOrDefault(t => t.Id == id);

    public TaskDto Create(CreateTaskDto dto)
    {
        var task = new TaskDto(_nextId++, dto.Title.Trim(), false);
        _tasks.Add(task);
        return task;
    }

    public bool Complete(int id)
    {
        var idx = _tasks.FindIndex(t => t.Id == id);
        if (idx < 0) return false;
        _tasks[idx] = _tasks[idx] with { IsDone = true };   // records: copy-with
        return true;
    }
}
```

## Part C — Register DI + endpoints
Replace `Program.cs`:
```csharp
using TaskApi;

var builder = WebApplication.CreateBuilder(args);
// Singleton so the in-memory list survives across requests (for THIS lab only):
builder.Services.AddSingleton<ITaskService, InMemoryTaskService>();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();
app.UseSwagger();
app.UseSwaggerUI();

var tasks = app.MapGroup("/api/tasks");

tasks.MapGet("/", (ITaskService svc) => Results.Ok(svc.GetAll()));

tasks.MapGet("/{id:int}", (int id, ITaskService svc) =>
    svc.Get(id) is { } t ? Results.Ok(t) : Results.NotFound());

tasks.MapPost("/", (CreateTaskDto dto, ITaskService svc) =>
{
    if (string.IsNullOrWhiteSpace(dto.Title))
        return Results.BadRequest(new { error = "Title is required" });
    var created = svc.Create(dto);
    return Results.Created($"/api/tasks/{created.Id}", created);
});

tasks.MapPost("/{id:int}/complete", (int id, ITaskService svc) =>
    svc.Complete(id) ? Results.NoContent() : Results.NotFound());

app.Run();
```
Add Swagger package if needed:
```bash
dotnet add package Swashbuckle.AspNetCore --version 6.6.2
```

## Part D — Exercise it
```bash
dotnet run        # note the port (say 5080); replace below if different
```
```bash
curl -s http://localhost:5080/api/tasks ; echo                       # []
curl -s -i -X POST http://localhost:5080/api/tasks \
  -H 'Content-Type: application/json' -d '{"title":"  write docs "}' | head -3
curl -s http://localhost:5080/api/tasks ; echo                       # [{"id":1,"title":"write docs","isDone":false}]
curl -s -i -X POST http://localhost:5080/api/tasks/1/complete | head -1   # HTTP/1.1 204
curl -s http://localhost:5080/api/tasks ; echo                       # isDone:true
curl -s -i http://localhost:5080/api/tasks/99 | head -1              # HTTP/1.1 404
curl -s -i -X POST http://localhost:5080/api/tasks \
  -H 'Content-Type: application/json' -d '{"title":""}' | head -1     # HTTP/1.1 400
```
✅ Observe: `201 Created` with a `Location` header, `204 No Content`, `404`, and `400`
for the empty title — model binding parsed the route ids and JSON body for you.

Open Swagger UI at `http://localhost:5080/swagger` and try the same calls.

## Part E — Compare with the real thing
```bash
diff <(echo "your Program.cs") /dev/null   # (just a reminder)
```
Open `<repo>/dotnet-course/apps/TaskApi/src/TaskApi/Program.cs` — it's the same shape,
but backed by **EF Core** (Module 08), with **Serilog** (Module 06) and **health
checks**. You've built the HTTP skeleton it hangs on.

## What you learned
- The builder → services → pipeline → endpoints → run structure.
- DI registration + injection; lifetimes (`Singleton` here, `Scoped` with EF next).
- Routing, route constraints, model binding, and `Results.*` status codes.

➡️ **[challenge.md](./challenge.md)** then [Module 08](../08-data-access-ef-core/).

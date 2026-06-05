# Challenge 07 — Reference Solution

### 1. DELETE + query filter
```csharp
tasks.MapDelete("/{id:int}", (int id, ITaskService svc) =>
    svc.Delete(id) ? Results.NoContent() : Results.NotFound());

tasks.MapGet("/", (ITaskService svc, bool? done) =>
{
    var all = svc.GetAll();
    var filtered = done is null ? all : all.Where(t => t.IsDone == done).ToList();
    return Results.Ok(filtered);
});
```
`bool? done` binds from the query string: `GET /api/tasks?done=true`. Add `Delete` to
the service (return false if not found).

### 2. Controller version
```csharp
using Microsoft.AspNetCore.Mvc;

[ApiController]
[Route("api/tasks")]
public class TasksController(ITaskService svc) : ControllerBase
{
    [HttpGet]
    public IActionResult GetAll() => Ok(svc.GetAll());

    [HttpGet("{id:int}")]
    public IActionResult Get(int id) =>
        svc.Get(id) is { } t ? Ok(t) : NotFound();

    [HttpPost]
    public IActionResult Create(CreateTaskDto dto)
    {
        if (string.IsNullOrWhiteSpace(dto.Title))
            return BadRequest(new { error = "Title is required" });
        var created = svc.Create(dto);
        return CreatedAtAction(nameof(Get), new { id = created.Id }, created);
    }
}
```
Register:
```csharp
builder.Services.AddControllers();
// ...
app.MapControllers();
```
> Same behavior, different style. `[ApiController]` adds automatic model-state
> validation and 400 responses; controllers scale better for large apps.

### 3. Lifetime bug
With `AddScoped`, a **new** `InMemoryTaskService` is created **per request**, so the
list is empty every time — your POSTed task "disappears" on the next request.
> `Singleton` kept one shared list alive (fine for an in-memory demo). Real apps use
> `Scoped` services backed by a **database**, so state lives in the DB, not in a
> per-request object. (EF Core's `DbContext` is registered `Scoped` for exactly this
> request-bounded lifetime — Module 08.)

### 4. Endpoint filter (stretch)
```csharp
tasks.MapPost("/", (CreateTaskDto dto, ITaskService svc) => { /* handler */ })
     .AddEndpointFilter(async (ctx, next) =>
     {
         var dto = ctx.GetArgument<CreateTaskDto>(0);
         if (dto.Title.Length > 50)
             return Results.BadRequest(new { error = "Title too long (max 50)" });
         return await next(ctx);
     });
```
> The cross-cutting check lives in the filter, keeping the handler focused.

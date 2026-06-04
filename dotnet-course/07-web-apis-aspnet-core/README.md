# Module 07 — Web APIs with ASP.NET Core

**Goal:** build and reason about HTTP APIs — the most common kind of .NET app you'll
support. You'll learn DI, the middleware pipeline, routing, and model binding by
building the first slices of **TaskApi**. ⏱️ ~2.5 h · 🎯 Prereq: 00–06.

---

## 1. The shape of an ASP.NET Core app

```csharp
var builder = WebApplication.CreateBuilder(args);   // 1. configure services (DI)
builder.Services.AddScoped<ITaskService, TaskService>();

var app = builder.Build();                           // 2. build the app
app.UseSerilogRequestLogging();                      // 3. middleware pipeline
app.MapGet("/api/tasks", (ITaskService svc) => svc.GetAllAsync());  // 4. endpoints
app.Run();                                            // 5. start listening
```
Two halves: **register services** (before `Build()`), then **configure the pipeline +
endpoints** (after). This split is the mental model for every ASP.NET Core app.

## 2. Dependency Injection (DI) — the backbone

You don't `new` your dependencies; you **register** them and the framework injects
them where needed (usually via constructor or endpoint parameter).
```csharp
builder.Services.AddScoped<ITaskService, TaskService>();  // "when someone needs ITaskService, give a TaskService"
```
Three **lifetimes**:
| Lifetime | One instance per… | Use for |
|----------|-------------------|---------|
| `AddSingleton` | whole app | stateless/shared services, caches |
| `AddScoped` | HTTP request | most services, **EF Core DbContext** |
| `AddTransient` | every injection | lightweight, stateless helpers |

Then just declare the dependency and it appears:
```csharp
app.MapGet("/api/tasks/{id:int}", (int id, ITaskService svc) => svc.GetAsync(id));
//                                          ^^^ injected from the container
```
DI is *why* we coded against `ITaskService` in Module 02 — it makes swapping
implementations and testing trivial.

## 3. The middleware pipeline

Each request flows through ordered **middleware** (and back):
```
request → [Serilog logging] → [exception handling] → [routing] → [auth] → endpoint → response
```
```csharp
app.UseSerilogRequestLogging();
app.UseExceptionHandler("/error");
app.MapHealthChecks("/health");
// ... endpoints
```
Order matters — e.g. exception handling must wrap the things it should catch.

## 4. Routing, model binding, results

**Minimal APIs** map routes to handler lambdas:
```csharp
var tasks = app.MapGroup("/api/tasks");
tasks.MapGet("/", (ITaskService s) => s.GetAllAsync());
tasks.MapGet("/{id:int}", (int id, ITaskService s) => s.GetAsync(id));   // route param + constraint
tasks.MapPost("/", (CreateTaskDto dto, ITaskService s) => s.CreateAsync(dto)); // body bound to dto
```
**Model binding** maps request parts to parameters: route values, query string, and
the JSON **body** (for complex types) automatically.

Return **`Results`** to control status codes:
```csharp
return created is null ? Results.NotFound() : Results.Ok(created);
Results.Created($"/api/tasks/{id}", created);   // 201 + Location header
Results.BadRequest(new { error = "Title is required" });   // 400
Results.NoContent();                              // 204
```

### Controllers (the other style)
The same API can be written with `[ApiController]` classes and `[HttpGet]` attributes.
Controllers suit larger apps (filters, model validation attributes, conventions);
minimal APIs suit small/fast services. **You'll see both in the wild** — TaskApi uses
minimal APIs; the challenge has you port one endpoint to a controller.

## 5. DTOs & validation

Accept/return **DTOs** (records), not your EF entities — it decouples your API
contract from your storage and avoids over-posting. Validate input (here, a non-empty
`Title`) and return `400` with a helpful message on bad input.

---

## Do the lab
Build TaskApi's HTTP layer step by step — DI, endpoints, model binding, status codes —
and exercise it with `curl`/Swagger. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Reference
Completed app: [`apps/TaskApi`](../apps/TaskApi/) — see `src/TaskApi/Program.cs`.

## Key terms
`WebApplication` builder · service registration · DI lifetimes (Singleton/Scoped/
Transient) · middleware pipeline · `MapGroup`/`MapGet`/`MapPost` · route constraints ·
model binding · `Results.*` / status codes · minimal API vs controllers · DTO

**Next →** [Module 08: Data Access with EF Core](../08-data-access-ef-core/)

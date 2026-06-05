# Sample App: `TaskApi`

The through-line for the **support phase** (Modules 05–09): a small ASP.NET Core +
EF Core Web API for managing tasks, with structured logging, DI, health checks, and
xUnit tests. This is the **completed reference** — you build your own copy
incrementally across the modules.

## Layout
```
TaskApi/
├── TaskApi.sln
├── src/TaskApi/                 # the Web API
│   ├── Program.cs               # builder, DI, Serilog, endpoints, health checks
│   ├── Models/TaskItem.cs       # EF entity
│   ├── Dtos/TaskDtos.cs         # request/response records
│   ├── Data/TaskDbContext.cs    # EF Core DbContext
│   ├── Services/                # ITaskService + TaskService (business logic)
│   └── appsettings*.json        # config + Serilog
└── tests/TaskApi.Tests/         # xUnit tests of TaskService (EF Core InMemory)
```

## Run
```bash
cd src/TaskApi
dotnet run                 # listens on http://localhost:5080 (see appsettings.json)
```
Then:
```bash
curl -s http://localhost:5080/health ; echo
curl -s -X POST http://localhost:5080/api/tasks \
  -H 'Content-Type: application/json' -d '{"title":"learn EF Core"}' ; echo
curl -s http://localhost:5080/api/tasks ; echo
curl -s -X POST http://localhost:5080/api/tasks/1/complete -i | head -1
```
Swagger UI (Development): <http://localhost:5080/swagger>.

## Test
```bash
cd <repo>/dotnet-course/apps/TaskApi
dotnet test                # runs the xUnit suite
```

## Notes
- The schema is created with `EnsureCreated()` on first run for **zero setup** (a
  local `tasks.db` SQLite file). **Module 08** covers switching to **EF Core
  migrations** (`dotnet ef migrations add` + `Database.Migrate()`).
- If the `.sln` ever gets out of sync, regenerate it:
  ```bash
  dotnet new sln -n TaskApi --force
  dotnet sln add src/TaskApi/TaskApi.csproj tests/TaskApi.Tests/TaskApi.Tests.csproj
  ```

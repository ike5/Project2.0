using Microsoft.EntityFrameworkCore;
using Serilog;
using TaskApi.Data;
using TaskApi.Dtos;
using TaskApi.Services;

var builder = WebApplication.CreateBuilder(args);

// --- Structured logging via Serilog, configured from appsettings.json ---
builder.Host.UseSerilog((context, config) =>
    config.ReadFrom.Configuration(context.Configuration));

// --- Dependency injection: register EF Core, the service, health checks, Swagger ---
var connectionString = builder.Configuration.GetConnectionString("Default")
    ?? "Data Source=tasks.db";
builder.Services.AddDbContext<TaskDbContext>(options => options.UseSqlite(connectionString));
builder.Services.AddScoped<ITaskService, TaskService>();
builder.Services.AddHealthChecks();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

// --- Create the SQLite schema on first run (simple local dev; Module 08 covers migrations) ---
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<TaskDbContext>();
    db.Database.EnsureCreated();
}

// --- Middleware pipeline ---
app.UseSerilogRequestLogging();
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.MapHealthChecks("/health");

// --- Endpoints (minimal API). Each handler receives ITaskService via DI. ---
var tasks = app.MapGroup("/api/tasks");

tasks.MapGet("/", async (ITaskService svc) =>
    Results.Ok(await svc.GetAllAsync()));

tasks.MapGet("/{id:int}", async (int id, ITaskService svc) =>
    await svc.GetAsync(id) is { } dto ? Results.Ok(dto) : Results.NotFound());

tasks.MapPost("/", async (CreateTaskDto dto, ITaskService svc) =>
{
    if (string.IsNullOrWhiteSpace(dto.Title))
        return Results.BadRequest(new { error = "Title is required" });
    var created = await svc.CreateAsync(dto);
    return Results.Created($"/api/tasks/{created.Id}", created);
});

tasks.MapPost("/{id:int}/complete", async (int id, ITaskService svc) =>
    await svc.CompleteAsync(id) ? Results.NoContent() : Results.NotFound());

tasks.MapDelete("/{id:int}", async (int id, ITaskService svc) =>
    await svc.DeleteAsync(id) ? Results.NoContent() : Results.NotFound());

app.Run();

// Exposed so the test project can spin up the app with WebApplicationFactory<Program>.
public partial class Program { }

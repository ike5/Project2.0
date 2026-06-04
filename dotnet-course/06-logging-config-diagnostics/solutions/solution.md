# Challenge 06 — Reference Solution

### 1. Structured over interpolated
```csharp
// before:
logger.LogInformation($"User {userId} placed order {orderId}");
// after:
logger.LogInformation("User {UserId} placed order {OrderId}", userId, orderId);
```
> The template version records `UserId` and `OrderId` as **structured fields**, so in
> a log store you can filter/aggregate ("all logs for OrderId=123") instead of
> grepping free text.

### 2. Correlation id middleware
```csharp
using Serilog.Context;

app.Use(async (ctx, next) =>
{
    var correlationId = ctx.Request.Headers["X-Correlation-ID"].FirstOrDefault()
        ?? Guid.NewGuid().ToString("N");
    ctx.Response.Headers["X-Correlation-ID"] = correlationId;
    using (LogContext.PushProperty("CorrelationId", correlationId))
        await next();
});
```
> Every log emitted while handling that request now includes `CorrelationId`. (Ensure
> `"Enrich": ["FromLogContext"]` is in the Serilog config — it is in TaskApi's appsettings.)

### 3. Validated Options
```csharp
using System.ComponentModel.DataAnnotations;

public class ApiOptions
{
    [Range(1, 500)]
    public int MaxTitleLength { get; set; } = 200;
    public string Owner { get; set; } = "unknown";
}

builder.Services.AddOptions<ApiOptions>()
    .Bind(builder.Configuration.GetSection("Api"))
    .ValidateDataAnnotations()
    .ValidateOnStart();      // app throws at startup if invalid
```
Set `"MaxTitleLength": 9999` in appsettings → `dotnet run` fails immediately with a
validation error. ✅ Fail-fast beats a runtime surprise.

### 4. Env-specific errors
```csharp
if (app.Environment.IsDevelopment())
    app.UseDeveloperExceptionPage();      // detailed stack traces (dev only)
else
    app.UseExceptionHandler("/error");    // generic handler in prod

app.MapGet("/error", () => Results.Problem("An unexpected error occurred."));
```
> Never leak stack traces to production clients; log the detail server-side, return a
> generic problem response.

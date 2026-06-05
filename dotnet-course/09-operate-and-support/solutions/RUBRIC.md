# Capstone A — Self-Assessment Rubric

Score your TaskApi honestly. Aim for "Solid" or better on every row.

| Capability | Needs work | Solid | Mastery |
|------------|-----------|-------|---------|
| **C# fluency** | copies snippets | writes idiomatic C# | uses records/LINQ/async naturally, explains value vs reference |
| **API design** | endpoints work | correct status codes, DTOs, DI | clean layering, validation, minimal-API *and* controller fluency |
| **Data (EF Core)** | CRUD works | migrations applied, queries translatable | reasons about N+1, server-side filtering, migration discipline |
| **Logging** | `Console.WriteLine` | structured `ILogger`/Serilog | correlation/scopes, right levels, exceptions logged with `ex` |
| **Config/secrets** | hardcoded | appsettings + environments + Options | user-secrets/env vars, validated options, no secrets in repo |
| **Testing** | none | xUnit covers the service | reproduce→test→fix reflex; meaningful assertions |
| **Debugging** | guesses | reads stack traces, uses breakpoints | drives exception breakpoints; diagnoses from logs alone |
| **Operations** | `dotnet run` only | publishes + meaningful `/health` | container/self-contained, readiness vs liveness, deploy-aware |
| **Diagnosis** | stuck | fixes with hints | identifies all four planted bugs from evidence + adds guards |

**You're ready for the next role rung when** you can take an unfamiliar .NET app,
stand it up, read its logs, and fix a reported bug with a test — calmly.

➡️ On to **Phase 2: Unity** ([Module 10](../../10-unity-setup-and-editor/)).

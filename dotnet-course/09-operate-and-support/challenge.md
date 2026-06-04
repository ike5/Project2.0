# Challenge 09 — Operate It

Solution in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Containerize.** Write a multi-stage `Dockerfile` for TaskApi, build it, run it,
   and hit `/health` and `/api/tasks` against the container. (If you don't have
   Docker, use `dotnet publish -p:PublishProfile=DefaultContainer` and inspect the
   produced image, or just explain the multi-stage build's two stages.)

2. **Graceful config.** Make the connection string come from configuration with a
   sensible fallback, and log (once, at startup) which database path is in use —
   so a "wrong DB" ticket is obvious from the logs.

3. **Diagnose blind.** Have someone apply *one* of the four planted bugs without
   telling you which. Identify it from symptoms + logs alone, state the evidence, and
   fix it. Add a test that would catch a regression.

4. **Readiness vs liveness (short answer).** Explain the difference between a liveness
   check ("is the process up?") and a readiness check ("can it serve traffic / are
   dependencies OK?"), and which one `AddDbContextCheck` contributes to.

## Success criteria
- [ ] A working container (or a correct explanation of the multi-stage build).
- [ ] Connection string is configurable with a fallback and logged at startup.
- [ ] You diagnosed a blind-applied bug with cited evidence and added a guarding test.
- [ ] Clear liveness-vs-readiness explanation.

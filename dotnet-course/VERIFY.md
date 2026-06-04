# End-to-End Verification

Run this after **Module 00** to confirm your toolchain works, and any time something
feels off. If every step passes, you're ready.

## 0. The SDK is installed
```bash
dotnet --version          # expect 8.0.x
dotnet --info             # lists SDKs/runtimes + your OS/arch
```
✅ A version prints. If `dotnet: command not found`, revisit Module 00 setup.

## 1. Create, build, and run a throwaway app
```bash
mkdir -p /tmp/dn-check && cd /tmp/dn-check
dotnet new console -n Hello
cd Hello
dotnet run
```
✅ Expected: `Hello, World!`

## 2. The fundamentals playground builds & runs
```bash
cd <repo>/dotnet-course/apps/console-playground
dotnet run
```
✅ Expected: a menu listing demos (types, OOP, LINQ, async); pick one and see output.

## 3. Tests run green
```bash
cd <repo>/dotnet-course/apps/TaskApi
dotnet test
```
✅ Expected: `Passed!  - Failed: 0` (the TaskApi solution includes an xUnit project).

## 4. The Web API runs and responds
```bash
cd <repo>/dotnet-course/apps/TaskApi/src/TaskApi
dotnet run
# in another terminal (note the port printed by dotnet run, often 5xxx):
curl -s http://localhost:5080/health ; echo
curl -s http://localhost:5080/api/tasks ; echo
curl -s -X POST http://localhost:5080/api/tasks \
  -H 'Content-Type: application/json' -d '{"title":"verify it works"}' ; echo
curl -s http://localhost:5080/api/tasks ; echo     # now includes your task
```
✅ Expected: `/health` returns `Healthy`; the POST returns the created task with an
`id`; the list includes it. (The DB is a local SQLite file created on first run.)

> The exact port is shown in `dotnet run` output (`Now listening on: http://localhost:XXXX`).
> Replace `5080` above with that port, or set it via `appsettings.json` /
> `ASPNETCORE_URLS`.

## 5. EF Core tooling installs
```bash
dotnet tool install --global dotnet-ef    # one-time; restart shell if PATH not updated
dotnet ef --version
```
✅ Expected: the EF Core tools version prints. (The reference `TaskApi` creates its
schema with `EnsureCreated()` for zero-setup; you'll add real **migrations** in
Module 08, where `dotnet ef migrations add` / `dotnet ef database update` come in.)

## 6. (Later — Phase 2) Unity
After Module 10 you'll also verify:
```text
- Unity Hub is installed and a Unity 6 LTS editor is added.
- A new project opens; pressing Play runs an empty scene with no errors.
```

---

🎉 **All green through step 5?** Your .NET environment is solid. Begin with
[Module 01](./01-csharp-fast-track-1/) (or [Module 00](./00-setup/) if you skipped setup).

Trouble? See [cheatsheets/debugging.md](./cheatsheets/debugging.md) and the
Troubleshooting section in [00-setup/README.md](./00-setup/README.md).

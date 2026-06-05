# .NET CLI Cheatsheet

The `dotnet` command is your hub for creating, building, running, testing, and
publishing .NET apps. Run any command with `--help` for details.

## Check your install
```bash
dotnet --version            # SDK version (expect 8.0.x)
dotnet --info               # SDKs, runtimes, OS/arch
dotnet --list-sdks
```

## Create projects (templates)
```bash
dotnet new list                         # all installed templates
dotnet new console   -n MyApp           # console app in ./MyApp
dotnet new classlib  -n MyLib           # class library
dotnet new web       -n MyWeb           # empty ASP.NET Core
dotnet new webapi    -n MyApi           # Web API (controllers)
dotnet new xunit     -n MyApp.Tests     # xUnit test project
dotnet new gitignore                    # a .NET .gitignore
```

## Solutions & project references
```bash
dotnet new sln -n MySolution            # create a solution
dotnet sln add MyApp/MyApp.csproj       # add a project to the solution
dotnet sln list
dotnet add MyApp/MyApp.csproj reference MyLib/MyLib.csproj   # project-to-project ref
```

## Packages (NuGet)
```bash
dotnet add package Serilog.AspNetCore               # add latest
dotnet add package Microsoft.EntityFrameworkCore.Sqlite --version 8.0.7
dotnet remove package Serilog.AspNetCore
dotnet restore                                       # restore all deps (usually implicit)
dotnet list package                                  # installed packages
dotnet list package --outdated
```

## Build & run
```bash
dotnet build                            # compile (Debug by default)
dotnet build -c Release                 # release config
dotnet run                              # build + run the project in this folder
dotnet run --project MyApp              # run a specific project
dotnet run -- arg1 arg2                 # pass args to your app (after --)
dotnet watch run                        # hot-reload: rebuild/rerun on file change
```

## Test
```bash
dotnet test                             # run all tests in the solution/project
dotnet test --filter "FullyQualifiedName~OrderTests"   # subset
dotnet test --logger "console;verbosity=detailed"
```

## Publish (deployable output)
```bash
dotnet publish -c Release -o ./publish                  # framework-dependent
dotnet publish -c Release -r osx-arm64 --self-contained # bundles the runtime (no install needed on target)
# common RIDs: osx-arm64, osx-x64, linux-x64, win-x64
```

## Entity Framework Core (tooling)
```bash
dotnet tool install --global dotnet-ef            # one-time
dotnet ef migrations add InitialCreate            # create a migration from your model
dotnet ef database update                         # apply migrations to the DB
dotnet ef migrations remove                        # undo the last (unapplied) migration
dotnet ef database drop
```

## Format & misc
```bash
dotnet format                           # apply code style/whitespace fixes
dotnet clean                            # remove build outputs (bin/, obj/)
```

---
**Daily loop:** `dotnet new` → edit code → `dotnet run` (or `dotnet watch run`) →
`dotnet test` → `dotnet publish`.

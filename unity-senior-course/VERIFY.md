# Verify

Cross-module commands to confirm your environment is set up correctly and
your course work is on track. Run these as you finish modules.

## Environment

```bash
# Unity Hub installed? (Mac)
ls "/Applications/Unity/Hub/Editor/" 2>/dev/null || ls "$HOME/Applications/Unity/Hub/Editor/"

# Unity version
"/Applications/Unity/Hub/Editor/6000.0.23f1/Unity.app/Contents/MacOS/Unity" -version 2>/dev/null \
  || ls "$HOME/Applications/Unity/Hub/Editor/"  # adjust to your version

# .NET 8 / C# 12 toolchain (for the modern C# module)
dotnet --version          # expect 8.x or 9.x
dotnet --list-sdks

# RenderDoc (GPU profiler)
which renderdoc           # or check Applications
```

## Per-module quick checks

### 00 — Setup

```bash
# Unity project exists
ls ~/UnityProjects/UnitySeniorLab/Library               # Unity has imported it
ls ~/UnityProjects/UnitySeniorLab/Packages/manifest.json
```

### 01 — Modern C#

```bash
# Confirm the lab project compiles
cd ~/UnityProjects/UnitySeniorLab
"$UNITY" -batchmode -quit -projectPath "$PWD" -logFile /tmp/unity.log
grep -E "error CS|Compilation succeeded" /tmp/unity.log
```

### 02 — Memory model

```bash
# Open the Memory Profiler package snapshot we generate
# (verification is interactive — see module README)
```

### 03 — Memory optimization

The "no per-frame allocations" rule: in the Memory Profiler, take a snapshot,
play for 5 seconds, take another. **Total GC alloc** in the second snapshot's
diff should be near zero (or only the cost of the system you intended).

### 04 — Native containers + Burst

In the Job, confirm `BurstCompile` is in effect:

```
Jobs > Worker Threads > YourJob > Compile time: AOT (Burst)
```

### 05 — DOTS / Entities

```bash
# Entities version pinned
grep -E "com\.unity\.entities" ~/UnityProjects/UnitySeniorLab/Packages/manifest.json
# expect "com.unity.entities": "1.3.x" or similar 1.x
```

### 06 — Rendering

Open `Window > Analysis > Frame Debugger`. The lab's "go look at your draw
calls" check should show **SRP Batcher: active** for all URP materials.

### 07 — Asset pipeline

```bash
# Build report exists
ls ~/UnityProjects/UnitySeniorLab/Build/Reports/BuildReport.json 2>/dev/null \
  || ls ~/UnityProjects/UnitySeniorLab/Logs/AssetImportWorker0.log
```

### 08 — Multiplayer

In PlayMode, you should see two player objects in the hierarchy, one tagged
`ServerPlayer`, one `ClientPlayer`. The ParrelSync check is optional.

### 09 — Async / threading

Profiler → CPU Usage → Hierarchy. After running the lab, there should be
**zero `JobScheduler` warnings about "managed allocations on the main
thread"**.

### 10 — Platform

```bash
# iOS: Xcode project generated
ls ~/UnityProjects/UnitySeniorLabBuild/iOS/

# Android: APK built
ls ~/UnityProjects/UnitySeniorLabBuild/Android/*.apk
```

### 11 — Profiling

Take a baseline frame time before and after the lab. **Lab should reduce
frame time**, not increase it.

### 12 — CI/CD

```bash
# Build script runs clean
~/UnityProjects/UnitySeniorLab/Tools/build.sh --platform=Linux64 --output=/tmp/u.build
ls -lh /tmp/u.build
```

### 13 — Senior patterns

The pool module: in PlayMode, spawn 1000 bullets. `GC.GetTotalMemory`
should be flat. Without the pool, it should grow.

### 14 — Capstone

```bash
# The capstone project builds clean, and runs at target FPS
# on your minimum-spec target device.
"$UNITY" -batchmode -quit -nographics \
  -projectPath ~/UnityProjects/SeniorCapstone \
  -buildTarget StandaloneLinux64 -executeMethod BuildScript.Linux
```

## Cross-module

```bash
# Confirm no committed Unity noise (Library/, Temp/, Logs/)
cd <course repo>
find . -path "*/Library" -prune -o -path "*/Temp" -prune -o -path "*/Logs" -prune -o -name "*.csproj" -print
# The above should print almost nothing; the only generated files you
# should see are the explicit scripts in unity-scripts/.

# Confirm no Resources.Load at runtime
grep -rn "Resources\.Load" unity-senior-course/unity-scripts/ 2>/dev/null | grep -v "Editor"
# Should be empty (or only Editor-time uses).
```

## When verification fails

1. Re-read the module's "Common pitfalls" section.
2. Confirm the Unity version matches the one in `00-setup/README.md`.
3. If a Burst/Entities lab fails, close and reopen Unity — the package
   manager sometimes needs a restart.
4. If IL2CPP builds fail on iOS, the most common cause is missing
   `link.xml`. Module 10 covers this.
5. Ask in the issue tracker, **with the log file** and the exact
   Unity version.

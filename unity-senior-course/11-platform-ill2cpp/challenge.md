# Challenge 11: Production-Grade Multi-Platform Build

**Time**: 4 hours
**Goal**: Build a small but complete game (3 scenes, an asset pipeline, save/load, networking) for iOS, Android, and a headless server, configure each platform's quirks, and document the build pipeline.

## Scope

A small turn-based multiplayer game: a 2-player arena where each player takes turns placing a unit. The game has a menu, a game scene, and an end scene. The asset pipeline uses Addressables. Save/load is JSON via a small schema. Networking is NGO host-only (one device hosts, the other connects).

The deliverable is a build that runs on iOS, Android, and a headless Linux server, with stripping bugs found and fixed, link.xml curated, build size tracked, and a build report generated.

## Requirements

### Platform configuration

1. **iOS build**:
   - IL2CPP, ARM64 only.
   - Managed Stripping = High.
   - Privacy manifest complete (declare analytics, no advertising tracking).
   - Bundle ID = `com.example.arenagame`.
   - Target iOS 15.0+, build for iPhone only.
   - Build a `.xcarchive` from a CLI script.

2. **Android build**:
   - IL2CPP, ARM64 only.
   - Managed Stripping = High.
   - Minimum API 24, Target API 34.
   - AAB format with Addressables.
   - Configure Play Asset Delivery for the "level data" Addressables group (fast follow mode).
   - Bundle ID = `com.example.arenagame`.

3. **Headless Linux server build**:
   - Dedicated server target, IL2CPP.
   - Strip all UI/audio components via `#if UNITY_SERVER`.
   - Run as `./ArenaServer.x86_64 -port 7777`.

### Build size budget

| Platform | Build size | Notes |
|----------|-----------|-------|
| iOS | <= 80 MB | App Thinning helps the device download |
| Android (AAB) | <= 60 MB | AAB is per-device |
| Linux server | <= 100 MB | No asset budget, code only |

If the build exceeds the budget, you must optimize: texture compression, mesh LODs, audio compression, dead code removal.

### Stripping robustness

1. Curate a `link.xml` that preserves all reflection-touched types.
2. Add `[Preserve]` attributes to JSON-deserializable models.
3. Test on a real iOS device. Confirm no `TypeLoadException` or `MissingMethodException` in the log.
4. Test on a real Android device. Same.
5. Document any types that required `[Preserve]` and why.

### Asset pipeline

1. Use Addressables for all level data and audio.
2. Configure the Addressables build for iOS, Android, and Linux server.
3. LocalBuildPath = `Library/com.unity.addressables/aa/iOS` etc. RemoteBuildPath is a stub (the local CDN).
4. Verify the streaming assets are correct for each platform.

### Save/load

1. Use `JsonUtility` for save data (AOT-friendly, no reflection).
2. Save to `Application.persistentDataPath`.
3. Use atomic file IO: write to `save.tmp`, rename to `save.dat` after flush.
4. Versioned save format: include a schema version int, reject incompatible versions.

### Build script

A `BuildScript.cs` with `#if UNITY_EDITOR` that:
- Configures the build target.
- Sets the scripting backend and architecture.
- Sets the bundle ID and version.
- Configures Addressables for the platform.
- Runs `BuildPipeline.BuildPlayer` with the right scenes.
- Saves a `build-report.json` with: build size, IL2CPP time, stripped type count, errors, warnings.

### CI integration

1. A GitHub Actions workflow (or shell script) that runs the build for each platform.
2. The workflow uploads the build artifacts and the build report.
3. The workflow runs `unity-il2cpp-validator` (or your custom validator) to check for known stripping issues.

## Deliverables

1. The Unity project, buildable for all three platforms.
2. A `BUILD.md` document with:
   - Build commands per platform.
   - link.xml contents and rationale.
   - Build report for the most recent build.
   - Known issues and workarounds.
3. A `PlatformNotes.md` for each platform:
   - iOS: device test results, build size, launch time, IL2CPP build time.
   - Android: same.
   - Linux server: same.
4. A `STRIPPING.md` listing all types that required `[Preserve]` and why.

## Acceptance criteria

| Criterion | Pass |
|-----------|------|
| iOS build runs on a real device | required |
| Android build runs on a real device | required |
| Linux server runs and accepts connections | required |
| Build size within budget | required |
| No reflection-caused crashes on any platform | required |
| link.xml curated | required |
| Build script automated | required |
| CI workflow runs the build | required |
| Save/load works on all platforms | required |
| Build report generated | required |

## Grading rubric

- **Platform correctness (30%)**: each platform builds and runs as specified.
- **Stripping robustness (25%)**: link.xml + [Preserve] + verified on device.
- **Build size discipline (20%)**: within budget, documented choices.
- **Build automation (15%)**: CLI script, CI workflow, build report.
- **Documentation (10%)**: BUILD.md, PlatformNotes.md, STRIPPING.md.

## Senior notes

Plan for IL2CPP from week 1. If you start with Mono and switch later, the bugs are catastrophic. The editor hides stripping issues. Every reflection-based deserializer is a time bomb.

Real devices from day 1. The simulator is not the platform. TestFlight and Play Internal Testing are free. Use them. A bug you find in week 1 is a 5-minute fix. A bug you find in week 50 is a 2-week delay.

TestFlight submission reveals configuration bugs you cannot anticipate. The first submission of any project is a "shake down" — you find missing icons, wrong bundle IDs, missing privacy manifests. Submit something in week 1, even if it's empty, to validate the pipeline.

Build size is a feature, not an accident. 50 MB in week 1 is easy. 200 MB in week 20 is normal. 800 MB in week 50 is the default. Track size from day 1. If it grows, you need to optimize. Texture compression, audio compression, mesh simplification, dead code removal — all of these are easier to do incrementally.

The App Store review process is asynchronous. Plan for a 24-48 hour review turnaround. Build a "we can ship a hotfix in 4 hours" capability: smoke tests in CI, automated screenshots, automatic TestFlight upload.

The lowest-spec device is the test target. A flagship iPhone runs everything. A 2018 Android shows you the real cost. Profile on the lowest-spec device. If you don't have one, buy one. It's a one-time cost that prevents shipping a broken game.

Memory budget on console is a hard line. If you exceed it, you fail certification. If you barely fit, you fail on memory spikes (shader compile, scene load, GC). Target 80% of the budget. Profile the worst case (longest session, most particles, full inventory).

Ship it.

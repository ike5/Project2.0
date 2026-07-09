# Module 13: Build Pipeline, CI/CD, Build Automation

This module covers what you need to ship software: Unity batch mode, the build script API, CI providers (GitHub Actions, Unity DevOps), store submission automation (fastlane), build size tracking, symbol upload for crash reporting, Addressables in CI, and headless server builds. By the end you will have a build pipeline that runs on every commit, on every platform, with size and symbol tracking, and a "we can ship a hotfix in 4 hours" capability.

## 1. Unity batch mode

`Unity -batchmode -quit -nographics -projectPath <path> -executeMethod <method>` is the entry point for any CI. The flags:

- `-batchmode`: no GUI, no popups, runs the method and exits.
- `-quit`: exit after the method returns.
- `-nographics`: no rendering, smaller footprint. Use for build-only runs.
- `-projectPath`: the Unity project root.
- `-executeMethod`: a static method in an editor script.
- `-buildTarget`: the build target (StandaloneWindows64, Android, iOS, etc.).
- `-logFile`: write logs to a file. Always use this in CI.

A typical CI invocation:
```bash
/Applications/Unity/Hub/Editor/6000.0.0f1/Unity \
  -batchmode -quit -nographics \
  -projectPath /path/to/project \
  -buildTarget Android \
  -executeMethod BuildScript.BuildAndroid \
  -logFile build.log
```

The method must be in an `Editor/` folder script, must be `public static`, must return `void` (or be async with `Awaitable`).

The senior pattern: `-nographics` for build-only runs, but NOT for tests. Tests need rendering for play mode tests. Omit `-nographics` when running tests.

## 2. Command line arguments

Unity has built-in command line args for common things. The most useful:

- `-buildTarget <target>`: switch the active build target before running the method.
- `-executeMethod <method>`: run a static method.
- `-logFile <path>`: write the editor log to a file.
- `-batchmode -quit -nographics`: headless mode.
- `-username <user> -password <pass> -serial <serial>`: activate Unity for CI. The license file approach is preferred in 2024+.
- `-force-clamped-single-instancing`: prevent two Unity instances on the same machine.

Custom args: read with `Environment.GetCommandLineArgs()`. The reference pattern is `--buildNumber=42` parsed in the build script.

## 3. BuildPipeline.BuildPlayer and IPreprocessBuildWithReport

`BuildPipeline.BuildPlayer(BuildPlayerOptions)` is the API. The options:
```csharp
var options = new BuildPlayerOptions
{
    scenes = new[] { "Assets/Scenes/Boot.unity" },
    locationPathName = "Builds/iOS",
    target = BuildTarget.iOS,
    targetGroup = BuildTargetGroup.iOS,
    options = BuildOptions.None,
    subtarget = (int)StandaloneBuildSubtarget.Server // for dedicated server
};
```

`IPreprocessBuildWithReport` lets you hook into the build process. Implement it to:
- Configure player settings before the build.
- Validate scenes.
- Generate Addressables content.
- Modify the build report.

```csharp
public class BuildPreprocessor : IPreprocessBuildWithReport
{
    public int callbackOrder => 0;

    public void OnPreprocessBuild(BuildReport report)
    {
        if (report.summary.platform == BuildTarget.iOS)
        {
            // iOS-specific pre-build setup
        }
    }
}
```

`IPostprocessBuildWithReport` runs after the build, useful for uploading symbols or copying files.

## 4. BuildReport

`BuildReport` is the result of a build. It contains:
- `summary`: total size, total time, errors, warnings.
- `steps`: per-step time (script compilation, IL2CPP, etc.).
- `files`: per-file output size.

The senior pattern: write a `build-report.json` after every build. CI parses it for size tracking and alerting.

```csharp
[Serializable]
class BuildReportJson
{
    public string platform;
    public ulong totalSize;
    public long elapsedMs;
    public int totalErrors;
    public int totalWarnings;
    public string outputPath;
    public List<BuildStepJson> steps;
}

[Serializable]
class BuildStepJson
{
    public string name;
    public long durationMs;
    public ulong size;
}
```

## 5. Custom build targets

The dedicated server build target (StandaloneBuildSubtarget.Server) is a recent addition. The 64-bit Linux server build is what most studios use for game servers.

```csharp
EditorUserBuildSettings.standaloneBuildSubtarget = StandaloneBuildSubtarget.Server;
var options = new BuildPlayerOptions
{
    scenes = new[] { "Assets/Scenes/Server.unity" },
    locationPathName = "Builds/Server/Server.x86_64",
    target = BuildTarget.StandaloneLinux64,
    subtarget = (int)StandaloneBuildSubtarget.Server
};
BuildPipeline.BuildPlayer(options);
```

The server build defines `UNITY_SERVER`. Use it to strip all UI/audio code:
```csharp
#if UNITY_SERVER
QualitySettings.vSyncCount = 0;
Application.targetFrameRate = 60;
// disable rendering
#endif
```

The headless server runs without a display. The OS sees it as a process. Run it under systemd, supervisord, or a container orchestrator (Kubernetes).

## 6. Cloud Build → Unity DevOps (UDS)

Unity Cloud Build was deprecated in 2023. The replacement is **Unity DevOps (UDS)**, part of Unity Gaming Services. The migration path:
- Existing Cloud Build projects must move to UDS Build Automation or to a third-party CI.
- New projects in 2024+ use UDS or GitHub Actions.

UDS Build Automation runs Unity builds on Unity's cloud. Pros: no CI server to maintain, the build is fast (Unity's hardware), the artifacts are hosted. Cons: cost, less control over the build environment.

GitHub Actions is the open alternative. Pros: free for public repos, full control, integrates with GitHub releases. Cons: you maintain the runners (or use hosted runners).

The senior default in 2026: **GitHub Actions for most projects, UDS for studios that don't want to maintain CI infrastructure**.

## 7. GitHub Actions for Unity

GitHub Actions uses the `game-ci/unity-builder` action:
```yaml
- uses: game-ci/unity-builder@v4
  with:
    targetPlatform: Android
    buildName: mygame-android
    unityVersion: 6000.0.0f1
  env:
    UNITY_LICENSE: ${{ secrets.UNITY_LICENSE }}
```

The action:
1. Activates Unity with the license file from secrets.
2. Runs the build with the specified target.
3. Uploads the artifacts to the workflow run.

The license file is created with `unity-license-setup` (a separate action). For most projects, store the license as a base64-encoded secret.

Caching the Library folder speeds up subsequent builds:
```yaml
- uses: actions/cache@v4
  with:
    path: Library
    key: Library-${{ hashFiles('Packages/manifest.json', 'Assets/**') }}
    restore-keys: Library-
```

The cache makes the second build 4x faster. Cache invalidates on `manifest.json` or `Assets/**` changes.

## 8. fastlane for store submission

fastlane automates App Store Connect, Google Play Console, Steam, and console submissions. The setup is per-platform:

**iOS**:
```ruby
lane :upload_testflight do
  build_app(scheme: "Unity-iPhone")
  upload_to_testflight
end
```

**Android**:
```ruby
lane :upload_play_internal do
  build_android_apk
  upload_to_play_store(track: "internal", aab: "app.aab")
end
```

**Steam**:
```ruby
lane :upload_steam do
  steam_upload(app_id: 12345, build_description: "CI build")
end
```

The senior pattern: fastlane runs after the Unity build in CI. The artifact from the Unity build is uploaded to the store. The build is fully automated from `git push` to "build available on TestFlight."

## 9. Build size tracking

Track build size over time. The senior pattern:

1. After every build, write `build-size.txt` to a known location.
2. CI compares against the previous build.
3. Alert if size grew by > 10%.

```yaml
- name: Check size
  run: |
    PREV=$(cat .previous-build-size)
    CURR=$(stat -c%s builds/mygame-android.aab)
    GROWTH=$((CURR * 100 / PREV))
    if [ $GROWTH -gt 110 ]; then
      echo "Build size grew from $PREV to $CURR bytes ($GROWTH%)"
      exit 1
    fi
    echo "$CURR" > .previous-build-size
```

A more sophisticated version graphs size over time and emails the team on regression.

## 10. Automatic symbol upload (IL2CPP line numbers)

IL2CPP compiles C# to C++ to native. Without symbols, a crash report is a hex address. With symbols, the crash report is a C# stack trace.

The senior pattern:
1. Unity produces a `.symbols.zip` (or `.so` with line tables).
2. CI uploads the symbols to your crash reporting backend.
3. The crash reports in the backend are deobfuscated automatically.

For Firebase Crashlytics:
```bash
firebase crashlytics:symbols:upload --app=APP_ID builds/il2cpp_symbols.zip
```

For Backtrace, Sentry, Bugsnag, similar commands.

The build script generates the symbols:
```csharp
PlayerSettings.SetIl2CppCompilerConfiguration(NamedBuildTarget.iOS, Il2CppCompilerConfiguration.Release);
// In a CI build, also generate symbols:
EditorUserBuildSettings.development = false; // Release build
PlayerSettings.SetIl2CppGenerateCodeOptimization(NamedBuildTarget.iOS, Il2CppCodeOptimization.Speed);
```

Then post-build:
```csharp
public class PostBuildSymbols : IPostprocessBuildWithReport
{
    public int callbackOrder => 0;

    public void OnPostprocessBuild(BuildReport report)
    {
        if (report.summary.platform == BuildTarget.iOS)
        {
            var symbolsPath = Path.Combine(report.summary.outputPath, "SymbolFiles");
            // zip the symbols, upload to crash reporting backend
        }
    }
}
```

Without symbols, your crash reports are useless. With symbols, they are actionable. This is the difference between "users are reporting crashes" and "I know exactly which line in `PlayerMotor.cs:42` is causing 80% of crashes."

## 11. Addressables in CI

Addressables content (the asset bundles) is built separately from the player build. The build script:

```csharp
public static void BuildAddressables()
{
    AddressableAssetSettings.CleanPlayerContent(AddressableAssetSettingsDefaultObject.Settings.ActivePlayerDataBuilder);
    AddressableAssetSettings.BuildPlayerContent(out var result);
    if (!string.IsNullOrEmpty(result.Error))
        throw new Exception($"Addressables build failed: {result.Error}");
}
```

The Addressables build outputs go to:
- `Library/com.unity.addressables/aa/<platform>/` (local)
- The configured remote path (S3, CDN, etc.)

In CI, the local path is fine for testing. For production, the remote path is a CDN that the player downloads from.

The senior pattern: build the player first, then build the Addressables. The Addressables build embeds the player's runtime settings. Build order matters.

## 12. Headless Linux build for server

A dedicated server is a Linux x86_64 build with `UNITY_SERVER` defined. The build:

```csharp
public static void BuildLinuxServer()
{
    EditorUserBuildSettings.standaloneBuildSubtarget = StandaloneBuildSubtarget.Server;
    EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.Standalone, BuildTarget.StandaloneLinux64);
    var options = new BuildPlayerOptions
    {
        scenes = new[] { "Assets/Scenes/Server.unity" },
        locationPathName = "Builds/Server/Server.x86_64",
        target = BuildTarget.StandaloneLinux64,
        subtarget = (int)StandaloneBuildSubtarget.Server,
        options = BuildOptions.None
    };
    BuildPipeline.BuildPlayer(options);
}
```

The server runs headless:
```bash
./Server.x86_64 -batchmode -nographics -port 7777 -logFile server.log
```

The server uses NGO host mode (module 9) to accept client connections. The container is typically a Docker image with the server binary, configuration, and any required shared libraries.

## 13. The full pipeline

A senior's pipeline for a small studio:

```
git push
  -> GitHub Actions triggered
    -> build-ios job: build iOS, upload to TestFlight
    -> build-android job: build AAB, upload to Play Internal
    -> build-linux-server job: build server, push to container registry
    -> build-windows job: build Windows, upload as artifact
  -> All jobs run in parallel
  -> On any failure, Slack notification
  -> On any size regression, Slack notification
  -> Daily: run integration tests
  -> Weekly: run soak tests (24-hour play, watch for leaks)
```

The total cost: $0 if you use GitHub-hosted runners and the repo is public. $200/month for a Unity Pro license and a fastlane subscription. A small studio pays for itself in the first month of saved engineering time.

## 14. Senior rules

1. Build on every commit. Don't accumulate changes without testing the build.
2. Track build size. A 10% growth without a feature change is a regression.
3. Upload symbols. Crash reports without symbols are useless.
4. Automate submission. From `git push` to "build on TestFlight" should be 30 minutes, not 2 days.
5. Test the build, not just the code. A passing test suite with a broken build is a false positive.
6. Use a license file, not username/password. License files survive rotation, password rotation breaks CI.
7. Cache the Library folder. Builds are 4x faster with cache.
8. Run the server build in CI. The server build catches different bugs than the client build.
9. Use the headless server build for production. A containerized server is easier to scale than a per-process server.
10. Don't deploy on Friday. A bug you find on Friday night is a weekend of pain.

## 15. Common pitfalls

- **License activation in CI fails**: the license file is in the wrong format, or the activation endpoint is unreachable. The `unity-license-setup` action handles this; use it.
- **Library cache grows unbounded**: the cache key needs a max size, or it eats all the runner's disk. Set a 5 GB cap.
- **Build size regression undetected**: you add an asset, the build grows by 50 MB, no one notices. The size tracking step catches it.
- **Symbols not uploaded**: the crash report backend has no symbols, the deobfuscation fails, the stack trace is hex addresses. Verify the symbol upload in CI.
- **Addressables built with the wrong player**: you build the player, then the Addressables, but the Addressables uses a stale player. Build Addressables after the player.
- **Headless server uses the desktop player's UI**: the server build has UI components that try to render. The `#if UNITY_SERVER` gate is the only way to strip them.
- **iOS build fails to sign in CI**: the developer cert is in the wrong keychain, or the provisioning profile is expired. Use `xcrun altool` or `fastlane match` to manage signing.
- **fastlane `upload_to_testflight` times out**: the IPA is too large (> 200 MB), or TestFlight is in maintenance. Check the build size and the Apple status page.

## What to read next

- Module 11: platform-specific build quirks.
- Module 12: profile the build to find the cost.
- Module 14: command pattern and save/load integrate with build automation.
- Module 9: NGO host startup in CI.

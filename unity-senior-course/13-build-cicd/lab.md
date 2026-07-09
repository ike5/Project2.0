# Lab 13: Build a CI Pipeline for a Unity Project

**Time**: 90 minutes
**Goal**: Set up a Unity project with a build script, run it locally, then move the build to GitHub Actions. Verify the build artifact, the build report, and the symbol upload.

## Setup (10 min)

1. New Unity 6 project. Push to a new GitHub repo.
2. Install `com.unity.addressables` and `com.unity.memoryprofiler`.
3. Create three scenes: `Boot`, `Menu`, `Game`.
4. Add a `BuildScript.cs` in `Assets/Editor/`.

## Part A: Build script (25 min)

`Assets/Editor/BuildScript.cs`:
```csharp
#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEditor.AddressableAssets;
using UnityEditor.AddressableAssets.Settings;
using UnityEditor.Build.Reporting;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.Rendering;

public static class BuildScript
{
    const string BuildDir = "Builds";
    const string BuildReportPath = "Builds/build-report.json";

    public static void BuildAndroid()
    {
        ConfigureAndroid();
        Build(BuildTarget.Android, BuildTargetGroup.Android, $"{BuildDir}/Android", BuildOptions.None);
    }

    public static void BuildIOS()
    {
        ConfigureIOS();
        Build(BuildTarget.iOS, BuildTargetGroup.iOS, $"{BuildDir}/iOS", BuildOptions.None);
    }

    public static void BuildLinuxServer()
    {
        ConfigureLinuxServer();
        EditorUserBuildSettings.standaloneBuildSubtarget = StandaloneBuildSubtarget.Server;
        Build(BuildTarget.StandaloneLinux64, BuildTargetGroup.Standalone, $"{BuildDir}/LinuxServer/Server.x86_64", BuildOptions.None);
    }

    static void ConfigureAndroid()
    {
        PlayerSettings.SetScriptingBackend(NamedBuildTarget.Android, ScriptingImplementation.IL2CPP);
        PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
        PlayerSettings.SetManagedStrippingLevel(NamedBuildTarget.Android, ManagedStrippingLevel.High);
        PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel24;
        PlayerSettings.Android.targetSdkVersion = AndroidSdkVersions.AndroidApiLevel34;
        EditorUserBuildSettings.buildAppBundle = true;
        PlayerSettings.applicationIdentifier = "com.example.arenagame";
    }

    static void ConfigureIOS()
    {
        PlayerSettings.SetScriptingBackend(NamedBuildTarget.iOS, ScriptingImplementation.IL2CPP);
        PlayerSettings.SetArchitecture(NamedBuildTarget.iOS, 1); // ARM64
        PlayerSettings.SetManagedStrippingLevel(NamedBuildTarget.iOS, ManagedStrippingLevel.High);
        PlayerSettings.applicationIdentifier = "com.example.arenagame";
    }

    static void ConfigureLinuxServer()
    {
        PlayerSettings.SetScriptingBackend(NamedBuildTarget.Standalone, ScriptingImplementation.IL2CPP);
        PlayerSettings.SetManagedStrippingLevel(NamedBuildTarget.Standalone, ManagedStrippingLevel.High);
    }

    static void Build(BuildTarget target, BuildTargetGroup group, string outputPath, BuildOptions options)
    {
        if (EditorUserBuildSettings.activeBuildTarget != target)
            EditorUserBuildSettings.SwitchActiveBuildTarget(group, target);

        // Build Addressables
        AddressableAssetSettings.CleanPlayerContent(AddressableAssetSettingsDefaultObject.Settings.ActivePlayerDataBuilder);
        AddressableAssetSettings.BuildPlayerContent(out var addrResult);
        if (!string.IsNullOrEmpty(addrResult.Error))
            throw new Exception($"Addressables build failed: {addrResult.Error}");

        // Build player
        Directory.CreateDirectory(Path.GetDirectoryName(outputPath) ?? ".");
        var playerOptions = new BuildPlayerOptions
        {
            scenes = new[] { "Assets/Scenes/Boot.unity", "Assets/Scenes/Menu.unity", "Assets/Scenes/Game.unity" },
            locationPathName = outputPath,
            target = target,
            targetGroup = group,
            options = options,
            subtarget = (int)EditorUserBuildSettings.standaloneBuildSubtarget
        };

        var report = BuildPipeline.BuildPlayer(playerOptions);
        var summary = report.summary;

        Debug.Log($"Build {target}: result={summary.result} size={summary.totalSize / 1024 / 1024}MB errors={summary.totalErrors} warnings={summary.totalWarnings}");

        WriteBuildReport(target.ToString(), summary);

        if (summary.result != BuildResult.Succeeded)
            throw new Exception($"Build {target} failed: {summary.result}");
    }

    static void WriteBuildReport(string platform, BuildSummary summary)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(BuildReportPath) ?? ".");
        File.WriteAllText(BuildReportPath, JsonUtility.ToJson(new BuildReportJson
        {
            platform = platform,
            result = summary.result.ToString(),
            totalSize = summary.totalSize,
            outputPath = summary.outputPath,
            totalErrors = (int)summary.totalErrors,
            totalWarnings = (int)summary.totalWarnings,
            totalDuration = (long)summary.totalTime.TotalSeconds,
            buildGuid = summary.guid.ToString()
        }, prettyPrint: true));
    }

    [Serializable]
    class BuildReportJson
    {
        public string platform;
        public string result;
        public ulong totalSize;
        public string outputPath;
        public int totalErrors;
        public int totalWarnings;
        public long totalDuration;
        public string buildGuid;
    }
}
#endif
```

## Part B: Local build (10 min)

1. Open a terminal in the project root.
2. Find your Unity install path.
3. Run:
   ```bash
   /Applications/Unity/Hub/Editor/6000.0.0f1/Unity \
     -batchmode -quit -nographics \
     -projectPath . \
     -buildTarget Android \
     -executeMethod BuildScript.BuildAndroid \
     -logFile build.log
   ```
4. Watch the build. After 5-10 minutes, you should see `Builds/Android/arenagame.aab` and `Builds/build-report.json`.

## Part C: Add GitHub Actions (30 min)

1. Create `.github/workflows/build.yml`:
   ```yaml
   name: Build
   on:
     push:
       branches: [main]
     pull_request:
       branches: [main]

   jobs:
     android:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
           with:
             lfs: true

         - uses: actions/cache@v4
           with:
             path: Library
             key: Library-${{ runner.os }}-${{ hashFiles('Packages/manifest.json', 'Assets/**', 'ProjectSettings/**') }}
             restore-keys: Library-${{ runner.os }}-

         - uses: game-ci/unity-builder@v4
           with:
             unityVersion: 6000.0.0f1
             targetPlatform: Android
             buildName: arenagame
             buildMethod: BuildScript.BuildAndroid
           env:
             UNITY_LICENSE: ${{ secrets.UNITY_LICENSE }}

         - uses: actions/upload-artifact@v4
           with:
             name: arenagame-android
             path: builds/arenagame/

         - name: Check build size
           run: |
             AAB=$(find builds -name "*.aab" | head -1)
             SIZE=$(stat -c%s "$AAB")
             SIZE_MB=$((SIZE / 1024 / 1024))
             echo "Build size: ${SIZE_MB}MB"
             if [ $SIZE_MB -gt 100 ]; then
               echo "Build exceeds 100MB budget"
               exit 1
             fi
   ```

2. Create a Unity license file. Use the Unity Hub or `unity-license-setup` action. Store as `UNITY_LICENSE` secret.

3. Push the workflow. The first run will take 15-20 minutes (no cache).

4. After the first run, subsequent runs should be 5-10 minutes (with cache).

## Part D: Verify the artifacts (10 min)

1. After the workflow runs, go to the Actions tab. Find the run.
2. Download the artifact. It should contain the .aab.
3. Open the build report. Check the size, time, and errors.

## Part E: Add size tracking (15 min)

Add a step that compares the build size to the previous main branch build:
```yaml
- name: Compare build size
  run: |
    CURRENT_SIZE=$(stat -c%s $(find builds -name "*.aab" | head -1))
    PREV_SIZE=$(cat .previous-build-size 2>/dev/null || echo $CURRENT_SIZE)
    GROWTH=$((CURRENT_SIZE * 100 / PREV_SIZE))
    if [ $GROWTH -gt 110 ]; then
       echo "Build size grew ${GROWTH}% (from $PREV_SIZE to $CURRENT_SIZE)"
       exit 1
    fi
    echo $CURRENT_SIZE > .previous-build-size
    echo "Size OK: ${GROWTH}% of previous"
```

Commit `.previous-build-size` to the repo (initial value: current size).

## Verification

1. Local build runs and produces a valid AAB.
2. GitHub Actions workflow runs the build.
3. Build artifact is downloadable from the Actions tab.
4. Build report is written and contains platform, size, time, errors.
5. Size tracking step passes (or fails appropriately).

## Common pitfalls

- **`Library/PlayerScriptAssemblies` cache invalidates too often**: the cache key includes `Assets/**`, which changes on every asset save. Use `hashFiles` on a more stable set: `Packages/manifest.json` + a project hash.
- **`UNITY_LICENSE` not set**: the `unity-license-setup` action fails. Add the secret.
- **Build target unavailable on Linux**: iOS and some console builds cannot be done on Linux. Use a Mac runner for iOS, or use Unity's cloud build (UDS).
- **Addressables not built**: the player build uses the old Addressables, missing assets at runtime. Always build Addressables first.
- **Build size growth undetected**: you forgot the size check step. Add it.
- **Symbol upload fails silently**: the post-build step throws but the workflow says "success." Use `set -e` in the script.
- **License rotation breaks CI**: the license file expires every 90 days. Set a calendar reminder to rotate.

## What we're testing

- Can you write a `BuildScript` that builds for a target with all the right settings?
- Can you run Unity in batch mode from the command line?
- Can you set up GitHub Actions for a Unity project?
- Can you cache the Library folder for fast CI?
- Can you track build size over time?

## Stretch goals

- Add a Linux server build job.
- Add an iOS build job on a Mac runner.
- Add a fastlane step that uploads the AAB to Play Console internal testing.
- Add a symbol upload step to your crash reporting backend.
- Add a Slack notification on build failure.

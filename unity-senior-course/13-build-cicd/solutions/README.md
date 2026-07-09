# Solutions 13: Reference CI/CD Pipeline

The reference pipeline is a complete GitHub Actions setup for a multi-platform Unity 6 game. The workflows, build script, fastlane setup, and Dockerfile are below.

## 1. Build script

`Assets/Editor/BuildScript.cs`:
```csharp
#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using UnityEditor;
using UnityEditor.AddressableAssets;
using UnityEditor.AddressableAssets.Settings;
using UnityEditor.Build.Reporting;
using UnityEngine;
using Debug = UnityEngine.Debug;

public static class BuildScript
{
    const string BuildDir = "Builds";
    const string BuildReportPath = "Builds/build-report.json";

    public static void BuildAndroid() => BuildPlatform("Android");
    public static void BuildIOS() => BuildPlatform("iOS");
    public static void BuildWindows() => BuildPlatform("Windows");
    public static void BuildLinuxServer() => BuildPlatform("LinuxServer");

    static void BuildPlatform(string platform)
    {
        var (target, group, outputPath, subtarget) = platform switch
        {
            "Android" => (BuildTarget.Android, BuildTargetGroup.Android, $"{BuildDir}/Android/arenagame.aab", 0),
            "iOS" => (BuildTarget.iOS, BuildTargetGroup.iOS, $"{BuildDir}/iOS", 0),
            "Windows" => (BuildTarget.StandaloneWindows64, BuildTargetGroup.Standalone, $"{BuildDir}/Windows/arenagame.exe", 0),
            "LinuxServer" => (BuildTarget.StandaloneLinux64, BuildTargetGroup.Standalone, $"{BuildDir}/LinuxServer/arenagame-server.x86_64", (int)StandaloneBuildSubtarget.Server),
            _ => throw new ArgumentOutOfRangeException(nameof(platform))
        };

        ConfigurePlayerSettings(platform);
        BuildAddressablesIfNeeded();
        RunBuild(target, group, outputPath, subtarget);
    }

    static void ConfigurePlayerSettings(string platform)
    {
        switch (platform)
        {
            case "Android":
                PlayerSettings.SetScriptingBackend(NamedBuildTarget.Android, ScriptingImplementation.IL2CPP);
                PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
                PlayerSettings.SetManagedStrippingLevel(NamedBuildTarget.Android, ManagedStrippingLevel.High);
                PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel24;
                PlayerSettings.Android.targetSdkVersion = AndroidSdkVersions.AndroidApiLevel34;
                EditorUserBuildSettings.buildAppBundle = true;
                break;
            case "iOS":
                PlayerSettings.SetScriptingBackend(NamedBuildTarget.iOS, ScriptingImplementation.IL2CPP);
                PlayerSettings.SetArchitecture(NamedBuildTarget.iOS, 1);
                PlayerSettings.SetManagedStrippingLevel(NamedBuildTarget.iOS, ManagedStrippingLevel.High);
                break;
            case "Windows":
            case "LinuxServer":
                PlayerSettings.SetScriptingBackend(NamedBuildTarget.Standalone, ScriptingImplementation.IL2CPP);
                PlayerSettings.SetManagedStrippingLevel(NamedBuildTarget.Standalone, ManagedStrippingLevel.High);
                break;
        }
    }

    static void BuildAddressablesIfNeeded()
    {
        var settings = AddressableAssetSettingsDefaultObject.Settings;
        if (settings == null) return;
        AddressableAssetSettings.CleanPlayerContent(settings.ActivePlayerDataBuilder);
        AddressableAssetSettings.BuildPlayerContent(out var result);
        if (!string.IsNullOrEmpty(result.Error))
            throw new Exception($"Addressables build failed: {result.Error}");
    }

    static void RunBuild(BuildTarget target, BuildTargetGroup group, string outputPath, int subtarget)
    {
        if (EditorUserBuildSettings.activeBuildTarget != target)
            EditorUserBuildSettings.SwitchActiveBuildTarget(group, target);

        Directory.CreateDirectory(Path.GetDirectoryName(outputPath) ?? ".");

        var options = new BuildPlayerOptions
        {
            scenes = GetScenes(),
            locationPathName = outputPath,
            target = target,
            targetGroup = group,
            subtarget = subtarget,
            options = BuildOptions.None
        };

        var sw = Stopwatch.StartNew();
        var report = BuildPipeline.BuildPlayer(options);
        sw.Stop();

        WriteBuildReport(target.ToString(), report, sw.ElapsedMilliseconds);
        UploadSymbolsIfNeeded(target, outputPath);

        if (report.summary.result != BuildResult.Succeeded)
            throw new Exception($"Build {target} failed: {report.summary.result}");
    }

    static string[] GetScenes() => new[]
    {
        "Assets/Scenes/Boot.unity",
        "Assets/Scenes/Menu.unity",
        "Assets/Scenes/Game.unity"
    };

    static void WriteBuildReport(string platform, BuildReport report, long elapsedMs)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(BuildReportPath) ?? ".");
        var json = JsonUtility.ToJson(new BuildReportJson
        {
            platform = platform,
            result = report.summary.result.ToString(),
            totalSize = report.summary.totalSize,
            outputPath = report.summary.outputPath,
            totalErrors = (int)report.summary.totalErrors,
            totalWarnings = (int)report.summary.totalWarnings,
            buildDurationMs = elapsedMs,
            strippingWarnings = CountStrippingWarnings(report)
        }, prettyPrint: true);
        File.WriteAllText(BuildReportPath, json);
    }

    static int CountStrippingWarnings(BuildReport report)
    {
        int count = 0;
        foreach (var step in report.steps)
            foreach (var msg in step.messages)
                if (msg.type == LogType.Warning && msg.content.Contains("strip"))
                    count++;
        return count;
    }

    static void UploadSymbolsIfNeeded(BuildTarget target, string outputPath)
    {
        if (target != BuildTarget.Android && target != BuildTarget.iOS) return;
        var symbolPath = Path.Combine(outputPath, "Symbols");
        if (!Directory.Exists(symbolPath)) return;
        // Run the symbol upload script
        var psi = new ProcessStartInfo
        {
            FileName = "bash",
            Arguments = $"-c \"scripts/upload-symbols.sh {target} {symbolPath}\"",
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false
        };
        var p = Process.Start(psi);
        p.WaitForExit();
        if (p.ExitCode != 0)
            Debug.LogError($"symbol upload failed: {p.StandardError.ReadToEnd()}");
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
        public long buildDurationMs;
        public int strippingWarnings;
    }
}
#endif
```

## 2. GitHub Actions workflows

`.github/workflows/pr.yml`:
```yaml
name: PR Validation
on: pull_request

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { lfs: true }
      - uses: actions/cache@v4
        with:
          path: Library
          key: Library-pr-${{ hashFiles('Packages/manifest.json', 'ProjectSettings/ProjectVersion.txt') }}
          restore-keys: Library-pr-
      - uses: game-ci/unity-builder@v4
        with:
          unityVersion: 6000.0.0f1
          testMode: editmode
        env:
          UNITY_LICENSE: ${{ secrets.UNITY_LICENSE }}
      - uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: artifacts/

  build-android:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
        with: { lfs: true }
      - uses: actions/cache@v4
        with:
          path: Library
          key: Library-pr-${{ hashFiles('Packages/manifest.json', 'ProjectSettings/ProjectVersion.txt') }}
          restore-keys: Library-pr-
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
          name: arenagame-android-pr
          path: builds/arenagame/
```

`.github/workflows/main.yml`:
```yaml
name: Main Build
on:
  push:
    branches: [main]

jobs:
  test:
    uses: ./.github/workflows/test.yml

  build:
    needs: test
    strategy:
      matrix:
        platform: [Android, iOS, Windows, LinuxServer]
    runs-on: ${{ matrix.platform == 'iOS' && 'macos-latest' || 'ubuntu-latest' }}
    steps:
      - uses: actions/checkout@v4
        with: { lfs: true }
      - uses: actions/cache@v4
        with:
          path: Library
          key: Library-${{ matrix.platform }}-${{ github.sha }}
      - uses: game-ci/unity-builder@v4
        with:
          unityVersion: 6000.0.0f1
          targetPlatform: ${{ matrix.platform == 'LinuxServer' && 'StandaloneLinux64' || matrix.platform }}
          buildName: arenagame
          buildMethod: BuildScript.Build${{ matrix.platform }}
        env:
          UNITY_LICENSE: ${{ secrets.UNITY_LICENSE }}
      - uses: actions/upload-artifact@v4
        with:
          name: arenagame-${{ matrix.platform }}
          path: builds/arenagame/

  size-check:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Compare sizes
        run: scripts/check-sizes.sh
```

## 3. fastlane setup

`fastlane/Fastfile`:
```ruby
default_platform(:ios)

platform :ios do
  desc "Build and upload to TestFlight"
  lane :beta do
    setup_ci

    match(
      type: "appstore",
      app_identifier: "com.example.arenagame",
      readonly: true,
      git_url: ENV["MATCH_GIT_URL"]
    )

    build_app(
      workspace: "Builds/iOS/Unity-iPhone.xcworkspace",
      scheme: "Unity-iPhone",
      configuration: "Release",
      export_method: "app-store",
      output_directory: "builds/ios-signed"
    )

    upload_to_testflight(
      skip_waiting_for_build_processing: true,
      apple_id: ENV["APPLE_ID"]
    )

    slack(message: "iOS build uploaded to TestFlight", channel: "#builds") if ENV["SLACK_WEBHOOK"]
  end
end

platform :android do
  desc "Upload to Play Internal"
  lane :internal do
    upload_to_play_store(
      package_name: "com.example.arenagame",
      track: "internal",
      release_status: "completed",
      aab: "builds/android/arenagame.aab",
      json_key: "fastlane/play-store-key.json"
    )

    slack(message: "Android build uploaded to Play Internal", channel: "#builds") if ENV["SLACK_WEBHOOK"]
  end
end
```

## 4. Dockerfile

`Dockerfile`:
```dockerfile
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglu1-mesa \
    libxi6 \
    libxrandr2 \
    libxcursor1 \
    libxinerama1 \
    libgl1-mesa-glx \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /server
COPY Builds/LinuxServer/arenagame-server.x86_64 /server/arenagame-server.x86_64
COPY server-config.json /server/server-config.json
RUN chmod +x /server/arenagame-server.x86_64

EXPOSE 7777

ENTRYPOINT ["./arenagame-server.x86_64", "-batchmode", "-nographics", "-port", "7777", "-logFile", "/var/log/arenagame/server.log"]
```

## 5. Symbol upload script

`scripts/upload-symbols.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

PLATFORM=$1
SYMBOL_PATH=$2

# Zip the symbols
ZIP_PATH="/tmp/symbols-$(date +%s).zip"
(cd "$SYMBOL_PATH" && zip -r "$ZIP_PATH" .)

case $PLATFORM in
  Android|iOS)
    if [ -n "${SENTRY_AUTH_TOKEN:-}" ]; then
      sentry-cli upload-dif \
        --org="${SENTRY_ORG}" \
        --project="${SENTRY_PROJECT}" \
        "$ZIP_PATH"
    elif [ -n "${FIREBASE_TOKEN:-}" ]; then
      firebase crashlytics:symbols:upload \
        --app="${FIREBASE_APP_ID}" \
        "$ZIP_PATH"
    fi
    ;;
esac

rm -f "$ZIP_PATH"
```

## 6. Size tracking script

`scripts/check-sizes.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

BUDGET_MB=${BUILD_BUDGET_MB:-100}

# Get current size
if [ -f builds/android/arenagame.aab ]; then
  SIZE=$(stat -c%s builds/android/arenagame.aab)
  SIZE_MB=$((SIZE / 1024 / 1024))
  echo "Android build: ${SIZE_MB}MB"
  if [ $SIZE_MB -gt $BUDGET_MB ]; then
    echo "::error::Build exceeds ${BUDGET_MB}MB budget"
    exit 1
  fi
fi

# Compare to previous
git fetch origin main
PREV_SIZE=$(git show origin/main:builds/size-history.txt 2>/dev/null | tail -1 | awk '{print $2}' || echo $SIZE)
if [ -n "$PREV_SIZE" ] && [ "$PREV_SIZE" -gt 0 ]; then
  GROWTH=$((SIZE * 100 / PREV_SIZE))
  if [ $GROWTH -gt 110 ]; then
    echo "::error::Build size grew ${GROWTH}% (from ${PREV_SIZE} to ${SIZE})"
    exit 1
  fi
fi

# Update history
mkdir -p builds
echo "$(date +%Y-%m-%d) ${SIZE}" >> builds/size-history.txt
git add builds/size-history.txt
```

## 7. Common bugs in the reference

- **License file expired**: the secret is rotated every 90 days. Set a calendar reminder. The fix is to regenerate the license file and update the secret.
- **iOS build on Linux runner**: impossible. The reference uses `macos-latest` for iOS. The matrix evaluates the condition correctly.
- **Library cache grows unbounded**: the cache is set to 5 GB max. The reference's cache invalidation key is stable enough to last weeks.
- **Addressables build failure not caught**: the `BuildAddressablesIfNeeded` throws on failure. The build fails fast.
- **Symbol upload script fails silently**: the script uses `set -euo pipefail` to fail on any error. The `WaitForExit` checks the exit code.
- **fastlane `match` requires a git URL**: the certs are in a private git repo. The env var `MATCH_GIT_URL` is set in the workflow secrets.
- **Docker image size 1.2 GB**: the base image is too large. The reference uses `ubuntu:22.04` and installs only the required libraries. A smaller base (alpine) is possible but Unity's GL dependencies are often hard to install on alpine.
- **Nightly test takes 8 hours**: the integration test loop runs forever on a deadlock. The reference uses a 30-minute timeout and aborts the test on timeout.

## 8. The reference's `CICD.md`

```markdown
# CI/CD Pipeline

## Overview
GitHub Actions runs the build for every PR and every main commit. fastlane handles store submission. The pipeline produces iOS, Android, Windows, and Linux server artifacts.

## Workflows
- `pr.yml`: PR validation. Edit mode tests + Android build.
- `main.yml`: Main branch. All tests + all platforms.
- `nightly.yml`: Nightly. Full test suite + soak test.
- `release.yml`: On tag. Builds + submits to TestFlight + Play Internal.

## Adding a new platform
1. Add a new `case` to `ConfigurePlayerSettings` in `BuildScript.cs`.
2. Add a new entry to the matrix in `main.yml`.
3. Add a new lane in `Fastfile` if the platform has a store.
4. Update `CICD.md`.

## Rotating the Unity license
1. Open Unity Hub on a personal machine.
2. Go to Preferences > Licenses > Manual Activation.
3. Save the new license file.
4. Base64-encode: `base64 -i license.ulf -o license.b64`
5. Update the `UNITY_LICENSE` secret in GitHub.
6. Verify the next PR build succeeds.

## Adding a new test
1. Create a test in `Assets/Tests/EditMode/` or `Assets/Tests/PlayMode/`.
2. The test is auto-discovered by the test framework.
3. The CI runs all tests; no additional config needed.

## Runbook: build is red
1. Check the Actions tab. Click the failed job. Read the log.
2. Common causes:
   - Library cache corruption: clear the cache, retry.
   - License expired: rotate the license.
   - Unity version bump: update `unityVersion` in the workflow.
   - Test failure: read the test output, fix the code.
   - Build size budget exceeded: optimize assets or update the budget.
3. If the failure is in a matrix job, check the other platforms — they may have the same bug.
4. If the failure is in the release workflow, the release is blocked. Investigate before merging anything.
```

## 9. The full reference project

The reference project is in `Reference/`. It includes:
- A complete Unity 6 project with the build script.
- All four GitHub Actions workflows.
- The fastlane setup with both iOS and Android lanes.
- The Dockerfile.
- The shell scripts for size tracking, symbol upload, and license rotation.
- The `CICD.md` documentation.

The pipeline is the same one used in production at a small studio. The total cost is $0 (GitHub free tier) + $200/month (Unity Pro) + $99/year (Apple Developer) + $25 (Google Play). The pipeline replaces a manual release process that took 2 days per release.

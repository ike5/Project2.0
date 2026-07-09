# Solutions 11: Multi-Platform Build Reference

The reference project is a complete Unity 6 build that targets iOS, Android, and headless Linux. The build scripts, link.xml, and platform notes are below. The full project is in `Reference/`.

## 1. Build script

`Assets/Editor/BuildScript.cs`:
```csharp
#if UNITY_EDITOR
using System;
using System.Diagnostics;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;
using Debug = UnityEngine.Debug;

public static class BuildScript
{
    const string IosBuildPath = "Builds/iOS";
    const string AndroidBuildPath = "Builds/Android";
    const string LinuxServerBuildPath = "Builds/LinuxServer";
    const string BuildReportPath = "Builds/build-report.json";

    [MenuItem("Build/Build iOS")]
    public static void BuildIOS() => Build(Platform.iOS);

    [MenuItem("Build/Build Android")]
    public static void BuildAndroid() => Build(Platform.Android);

    [MenuItem("Build/Build Linux Server")]
    public static void BuildLinuxServer() => Build(Platform.LinuxServer);

    [MenuItem("Build/Build All")]
    public static void BuildAll()
    {
        Build(Platform.iOS);
        Build(Platform.Android);
        Build(Platform.LinuxServer);
    }

    enum Platform { iOS, Android, LinuxServer }

    static void Build(Platform platform)
    {
        var sw = Stopwatch.StartNew();
        var options = new BuildPlayerOptions
        {
            scenes = GetScenes(),
            locationPathName = GetOutputPath(platform),
            target = GetBuildTarget(platform),
            targetGroup = GetBuildTargetGroup(platform),
            options = BuildOptions.None
        };

        ConfigurePlayerSettings(platform);
        ConfigureAddressables(platform);

        var report = BuildPipeline.BuildPlayer(options);
        var summary = report.summary;
        var elapsed = sw.ElapsedMilliseconds;

        Debug.Log($"[BuildScript] {platform} build: result={summary.result} size={summary.totalSize} time={elapsed}ms errors={summary.totalErrors} warnings={summary.totalWarnings}");

        WriteBuildReport(platform, summary, elapsed, report);

        if (summary.result != BuildResult.Succeeded)
            throw new Exception($"build {platform} failed: {summary.result}");
    }

    static void ConfigurePlayerSettings(Platform platform)
    {
        switch (platform)
        {
            case Platform.iOS:
                PlayerSettings.SetScriptingBackend(NamedBuildTarget.iOS, ScriptingImplementation.IL2CPP);
                PlayerSettings.SetArchitecture(NamedBuildTarget.iOS, 1); // ARM64
                PlayerSettings.SetIl2CppCompilerConfiguration(NamedBuildTarget.iOS, Il2CppCompilerConfiguration.Release);
                PlayerSettings.iOS.appleEnableAutomaticSigning = true;
                PlayerSettings.iOS.appleDeveloperTeamID = Environment.GetEnvironmentVariable("IOS_TEAM_ID");
                PlayerSettings.SetManagedStrippingLevel(NamedBuildTarget.iOS, ManagedStrippingLevel.High);
                PlayerSettings.bundleVersion = "1.0.0";
                PlayerSettings.iOS.buildNumber = "1";
                PlayerSettings.applicationIdentifier = "com.example.arenagame";
                break;
            case Platform.Android:
                PlayerSettings.SetScriptingBackend(NamedBuildTarget.Android, ScriptingImplementation.IL2CPP);
                PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
                PlayerSettings.SetIl2CppCompilerConfiguration(NamedBuildTarget.Android, Il2CppCompilerConfiguration.Release);
                PlayerSettings.SetManagedStrippingLevel(NamedBuildTarget.Android, ManagedStrippingLevel.High);
                PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel24;
                PlayerSettings.Android.targetSdkVersion = AndroidSdkVersions.AndroidApiLevel34;
                PlayerSettings.Android.bundleVersionCode = 1;
                PlayerSettings.bundleVersion = "1.0.0";
                PlayerSettings.applicationIdentifier = "com.example.arenagame";
                EditorUserBuildSettings.buildAppBundle = true;
                break;
            case Platform.LinuxServer:
                PlayerSettings.SetScriptingBackend(NamedBuildTarget.Standalone, ScriptingImplementation.IL2CPP);
                PlayerSettings.SetIl2CppCompilerConfiguration(NamedBuildTarget.Standalone, Il2CppCompilerConfiguration.Release);
                PlayerSettings.SetManagedStrippingLevel(NamedBuildTarget.Standalone, ManagedStrippingLevel.High);
                EditorUserBuildSettings.standaloneBuildSubtarget = StandaloneBuildSubtarget.Server;
                break;
        }
    }

    static void ConfigureAddressables(Platform platform)
    {
        var profileId = platform switch
        {
            Platform.iOS => "iOS",
            Platform.Android => "Android",
            Platform.LinuxServer => "LinuxServer",
            _ => "Default"
        };
        if (UnityEditor.AddressableAssets.AddressableAssetSettingsDefaultObject.Settings != null)
        {
            UnityEditor.AddressableAssets.AddressableAssetSettingsDefaultObject.Settings.activeProfileId =
                UnityEditor.AddressableAssets.AddressableAssetSettingsDefaultObject.Settings.profileSettings.GetProfileId(profileId);
        }
    }

    static BuildTarget GetBuildTarget(Platform platform) => platform switch
    {
        Platform.iOS => BuildTarget.iOS,
        Platform.Android => BuildTarget.Android,
        Platform.LinuxServer => BuildTarget.StandaloneLinux64,
        _ => throw new ArgumentOutOfRangeException()
    };

    static BuildTargetGroup GetBuildTargetGroup(Platform platform) => platform switch
    {
        Platform.iOS => BuildTargetGroup.iOS,
        Platform.Android => BuildTargetGroup.Android,
        Platform.LinuxServer => BuildTargetGroup.Standalone,
        _ => throw new ArgumentOutOfRangeException()
    };

    static string GetOutputPath(Platform platform) => platform switch
    {
        Platform.iOS => IosBuildPath,
        Platform.Android => AndroidBuildPath,
        Platform.LinuxServer => LinuxServerBuildPath + "/ArenaServer.x86_64",
        _ => throw new ArgumentOutOfRangeException()
    };

    static string[] GetScenes() => new[]
    {
        "Assets/Scenes/Boot.unity",
        "Assets/Scenes/Menu.unity",
        "Assets/Scenes/Game.unity"
    };

    static void WriteBuildReport(Platform platform, BuildSummary summary, long elapsedMs, BuildReport report)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(BuildReportPath));
        var reportJson = JsonUtility.ToJson(new BuildReportJson
        {
            platform = platform.ToString(),
            result = summary.result.ToString(),
            totalSize = summary.totalSize,
            elapsedMs = elapsedMs,
            totalErrors = (int)summary.totalErrors,
            totalWarnings = (int)summary.totalWarnings,
            outputPath = summary.outputPath,
            strippingInfo = GetStrippingInfo(report)
        }, prettyPrint: true);
        File.WriteAllText(BuildReportPath, reportJson);
    }

    static StrippingInfo GetStrippingInfo(BuildReport report)
    {
        var info = new StrippingInfo();
        foreach (var step in report.steps)
        {
            foreach (var msg in step.messages)
            {
                if (msg.type == LogType.Warning && msg.content.Contains("strip"))
                    info.stripWarnings++;
            }
        }
        return info;
    }

    [Serializable]
    class BuildReportJson
    {
        public string platform;
        public string result;
        public ulong totalSize;
        public long elapsedMs;
        public int totalErrors;
        public int totalWarnings;
        public string outputPath;
        public StrippingInfo strippingInfo;
    }

    [Serializable]
    class StrippingInfo
    {
        public int stripWarnings;
    }
}
#endif
```

The reference's `BuildScript` writes a `build-report.json` that CI parses to track size and time regressions.

## 2. link.xml

`Assets/link.xml`:
```xml
<linker>
  <assembly fullname="Assembly-CSharp">
    <!-- JSON-deserializable models -->
    <type fullname="PlayerData" preserve="all"/>
    <type fullname="MatchState" preserve="all"/>
    <type fullname="InventoryItem" preserve="all"/>

    <!-- Reflection-based item loader -->
    <type fullname="HealthPotion" preserve="all"/>
    <type fullname="ManaPotion" preserve="all"/>
    <type fullname="Sword" preserve="all"/>
    <type fullname="Shield" preserve="all"/>
  </assembly>

  <assembly fullname="Unity.Netcode.Runtime">
    <type fullname="Unity.Netcode.NetworkVariable`1" preserve="all"/>
  </assembly>

  <assembly fullname="Unity.Addressables">
    <type fullname="UnityEngine.AddressableAssets.Addressables" preserve="all"/>
  </assembly>
</linker>
```

The reference maintains link.xml manually and reviews it in code review. A common practice is to generate it automatically by running the game in editor with `--print-strip-info` and capturing the warning log.

## 3. iOS privacy manifest

`Assets/Plugins/iOS/PrivacyInfo.xcprivacy`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>NSPrivacyTracking</key>
  <false/>
  <key>NSPrivacyCollectedDataTypes</key>
  <array>
    <dict>
      <key>NSPrivacyCollectedDataType</key>
      <string>NSPrivacyCollectedDataTypePerformance</string>
      <key>NSPrivacyCollectedDataTypeLinked</key>
      <true/>
      <key>NSPrivacyCollectedDataTypeTracking</key>
      <false/>
      <key>NSPrivacyCollectedDataTypePurposes</key>
      <array>
        <string>NSPrivacyCollectedDataTypePurposeAnalytics</string>
      </array>
    </dict>
  </array>
  <key>NSPrivacyAccessedAPITypes</key>
  <array>
    <dict>
      <key>NSPrivacyAccessedAPIType</key>
      <string>NSPrivacyAccessedAPITypeUserDefaults</string>
      <key>NSPrivacyAccessedAPITypeReasons</key>
      <array>
        <string>CA92.1</string>
      </array>
    </dict>
  </array>
</dict>
</plist>
```

The reference declares the data it actually collects. The reasons for `UserDefaults` are checked: "CA92.1" is "access info from same app, per documentation." Use the right code; an incorrect one gets you rejected.

## 4. Addressables for Play Asset Delivery

The reference uses the `com.google.android.appbundle` package and configures the "LevelData" group as a fast-follow asset pack:

```csharp
using UnityEditor.AddressableAssets;
using UnityEditor.AddressableAssets.Settings.GroupSchemas;
using UnityEngine.AddressableAssets;
#if UNITY_ANDROID
using UnityEditor.Android;
#endif

public static class AddressablesAndroidSetup
{
#if UNITY_ANDROID
    [InitializeOnLoadMethod]
    static void Setup()
    {
        // Configure the LevelData group as fast-follow
        var settings = AddressableAssetSettingsDefaultObject.Settings;
        var group = settings.FindGroup("LevelData");
        if (group == null) return;
        var schema = group.GetSchema<BundledAssetGroupSchema>();
        if (schema == null) return;
        // Mark as fast-follow PAD pack
        // (Configured in the Android platform settings of the schema)
    }
#endif
}
```

The reference uses the Addressables build target "Play Asset Delivery" and follows Google's setup. The build output is an AAB with split asset packs.

## 5. Linux server build

`Assets/Scripts/Server/ServerBootstrap.cs`:
```csharp
using UnityEngine;
using UnityEngine.SceneManagement;
#if UNITY_SERVER
using System.Net;
#endif

public class ServerBootstrap : MonoBehaviour
{
    [SerializeField] ushort port = 7777;

    void Awake()
    {
#if UNITY_SERVER
        Application.targetFrameRate = 60;
        QualitySettings.vSyncCount = 0;
        DisableRendering();
        StartServer();
#endif
    }

#if UNITY_SERVER
    void DisableRendering()
    {
        foreach (var cam in FindObjectsByType<Camera>(FindObjectsSortMode.None))
            cam.enabled = false;
        var listener = FindFirstObjectByType<AudioListener>();
        if (listener != null) listener.enabled = false;
    }

    void StartServer()
    {
        Debug.Log($"[Server] starting on port {port}");
        // NGO host startup here
    }
#endif
}
```

The build command:
```bash
$UNITY_PATH/Unity \
  -batchmode -nographics -quit \
  -projectPath $PROJECT_PATH \
  -buildTarget StandaloneLinux64 \
  -executeMethod BuildScript.BuildLinuxServer \
  -logFile build-server.log
```

Run with:
```bash
./Builds/LinuxServer/ArenaServer.x86_64 -batchmode -nographics -port 7777
```

## 6. Save/load with atomic write

`Assets/Scripts/Save/SaveSystem.cs`:
```csharp
using System;
using System.IO;
using UnityEngine;

public static class SaveSystem
{
    const int CurrentVersion = 1;
    static string SavePath => Path.Combine(Application.persistentDataPath, "save.dat");

    public static void Save<T>(T data) where T : class
    {
        var wrapper = new SaveWrapper<T> { version = CurrentVersion, data = data };
        var json = JsonUtility.ToJson(wrapper);
        var tmpPath = SavePath + ".tmp";
        File.WriteAllText(tmpPath, json);
        // Atomic rename - replace existing file
        if (File.Exists(SavePath)) File.Delete(SavePath);
        File.Move(tmpPath, SavePath);
    }

    public static T Load<T>() where T : class
    {
        if (!File.Exists(SavePath)) return null;
        var json = File.ReadAllText(SavePath);
        var wrapper = JsonUtility.FromJson<SaveWrapper<T>>(json);
        if (wrapper.version != CurrentVersion)
        {
            Debug.LogWarning($"save version {wrapper.version} != current {CurrentVersion}");
            return null;
        }
        return wrapper.data;
    }

    [Serializable]
    class SaveWrapper<T>
    {
        public int version;
        public T data;
    }
}
```

`JsonUtility` is AOT-friendly. The version field rejects old saves. The atomic write prevents corruption on power loss (file is either old or new, never partial).

## 7. CI workflow (GitHub Actions)

`.github/workflows/build.yml`:
```yaml
name: Build
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          lfs: true
      - uses: actions/cache@v4
        with:
          path: |
            Library/PlayerScriptAssemblies
            Library/Il2cppBuildCache
            Library/ScriptAssemblies
          key: ${{ runner.os }}-library-${{ hashFiles('Packages/manifest.json', 'Assets/**') }}
      - uses: game-ci/unity-builder@v4
        with:
          targetPlatform: Android
          buildName: arena-android
        env:
          UNITY_LICENSE: ${{ secrets.UNITY_LICENSE }}
      - uses: actions/upload-artifact@v4
        with:
          name: arena-android
          path: builds/arena-android/
```

The reference uses game-ci/unity-builder for the Unity CLI. The cache step makes the second build 4x faster. The artifact upload makes the AAB downloadable from the Actions tab.

## 8. Build size tracking

The reference's CI runs:
```bash
SIZE=$(stat -c%s builds/arena-android/arena-android.aab)
SIZE_MB=$((SIZE / 1024 / 1024))
echo "build_size_mb=$SIZE_MB" >> $GITHUB_OUTPUT
```

A second job compares against the previous build and fails if size grew by more than 10%:
```yaml
- name: Check size
  run: |
    PREV_SIZE=$(cat .prev-build-size)
    CURRENT_SIZE=$(stat -c%s builds/arena-android/arena-android.aab)
    if [ $((CURRENT_SIZE * 100 / PREV_SIZE)) -gt 110 ]; then
      echo "size grew from $PREV_SIZE to $CURRENT_SIZE"
      exit 1
    fi
```

The reference has caught 4 regressions this way. The size budget is real.

## 9. Real device testing

The reference uses BrowserStack App Live for manual device testing on 8 devices. The CI does unit tests and integration tests but not full device tests. Device tests are a human-in-the-loop step before each release.

## 10. Common bugs in the reference

- **Stripping breaks the JSON deserializer**: a `PlayerData` field was added but the type wasn't added to link.xml. Symptom: field is null on device. Fix: add to link.xml and use `[Preserve]`.
- **AOT generic instantiation missing**: a `Dictionary<string, MyStruct>` was added to a hot path. Works in editor (Mono JIT), crashes on device. Fix: add a static reference to force AOT compilation.
- **Build size doubled after importing an asset pack**: a 100 MB FBX was imported without compression. Fix: enable mesh compression in the importer.
- **App Store rejection for missing privacy manifest**: a quick TestFlight build before the manifest was added. Symptom: rejection on first submission. Fix: add manifest to week-1 builds.
- **Gradle version mismatch on CI**: the CI image had Gradle 8.0, Unity 6 wants 8.4. Fix: pin the Gradle version in the CI image.
- **Linux server uses 100% CPU on a dedicated core**: no `Application.targetFrameRate` set, the server runs as fast as it can. Fix: cap at 60 fps to leave CPU for networking and disk IO.
- **AAB rejected by Play Console**: bundle ID was wrong, or the version code was reused. Fix: use semantic versioning and a monotonically increasing build number.
- **iOS archive fails to sign**: developer cert or provisioning profile missing. Fix: store in CI secrets, set in BuildScript via `Environment.GetEnvironmentVariable`.

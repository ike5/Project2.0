# Module 11: iOS, Android, Console, IL2CPP, Scripting Backends

This module covers what you need to know to ship a Unity game on iOS, Android, and consoles. The single biggest determinant of platform success is whether you planned for the platform on day one, not on day 90.

## 1. Mono vs IL2CPP

Unity supports two scripting backends: **Mono** (just-in-time compiled, default in editor) and **IL2CPP** (ahead-of-time compiled, default on most platforms). Editor always uses Mono. Builds can be either, but most production builds use IL2CPP.

- **Mono (JIT)**: compiles C# IL to native code at runtime. Fast iteration, supports `Reflection.Emit`, easy dynamic code. Slower startup, larger memory, banned on iOS and most consoles.
- **IL2CPP (AOT)**: compiles C# IL to C++ at build time, then to native code via the platform compiler. Slower build, faster runtime, smaller memory. Required on iOS, Android (recommended), PS5, Xbox Series, Switch.

The senior default: **IL2CPP everywhere you can**. The exception is WebGL, which has its own IL2CPP variant with limitations.

## 2. IL2CPP build time

IL2CPP builds are slow. A full project build with IL2CPP can take 20-60 minutes for a mid-size project. This is why CI build servers (module 13) matter.

- Incremental IL2CPP builds: Unity caches IL2CPP output. A no-change rebuild is fast (~1-2 min). A change to a frequently-included assembly can be slow (re-process the whole assembly).
- IL2CPP+ARM64: full rebuild per architecture. ARM64-only is faster than ARMv7+ARM64.
- Stripping level: aggressive stripping (High) takes longer to build because link.xml resolution runs more analysis.

CI tip: cache the Library/PlayerScriptAssemblies and Library/Il2cppBuildCache directories between builds. The first build is slow, subsequent builds are minutes.

## 3. AOT vs JIT limitations

IL2CPP is AOT. Several C# features do not work or work partially:

- **`Reflection.Emit`**: not supported. No runtime code generation.
- **Dynamic method dispatch**: limited. Generic virtual methods with reference type arguments work; with value type arguments, each unique value type is a separate instantiation that must be AOT-compiled.
- **Reflection over types that are stripped**: types stripped by managed code stripping throw `TypeLoadException` when accessed via reflection. This is the #1 source of "works in editor, crashes on device."
- **`System.Reflection.Emit.OpCodes`**: not supported.
- **`System.CodeDom`**: not supported.
- **`CSharpCodeProvider` / `Roslyn` at runtime**: not supported.

If your code uses `Type.GetType("MyType")` and `MyType` was stripped, the call returns null or throws. The fix is `link.xml` to preserve the type, or `[Preserve]` attribute, or explicit static reference.

## 4. Managed code stripping

Unity strips unused managed code to reduce build size. Three levels:

- **Low (disabled)**: nothing is stripped. Build is large. Use for debugging stripping bugs.
- **Medium (default for IL2CPP)**: unreachable code is removed. Public types in your code are kept. Some reflection-friendly paths are removed.
- **High**: aggressive. Removes everything not directly referenced. Smallest builds but most reflection bugs.

Stripping is the cause of 90% of "works in editor, fails on build" bugs. The editor does not strip (Mono JIT loads everything). The build strips aggressively, removing types you only access via reflection.

The fix is a `link.xml` file in `Assets/`:

```xml
<linker>
  <assembly fullname="MyGame" preserve="all"/>
  <assembly fullname="MyGame.Data" preserve="all"/>
  <assembly fullname="Newtonsoft.Json">
    <type fullname="Newtonsoft.Json.Converters.CustomConverter" preserve="all"/>
  </assembly>
</linker>
```

The link.xml is the override. Use `[Preserve]` attributes on classes/methods you need at runtime via reflection:

```csharp
[Preserve]
public class ReflectionAccessedType
{
    [Preserve]
    public void ReflectionAccessedMethod() { }
}
```

Stripping logs go to `il2cpp_out.log` (or Player log on device). Search for "stripped" or "removed" to see what got removed.

## 5. iOS specifics

### 5.1 64-bit only

Since 2018, Apple requires 64-bit iOS apps. Unity 6 with IL2CPP is 64-bit by default. There is no 32-bit iOS support.

### 5.2 App Store requirements

- **Apple Silicon**: Macs are now Apple Silicon by default. CI runners must be Apple Silicon or the build will fall back to Rosetta, which is slower and may have symbol issues. M1/M2/M3 Mac minis are common CI runners.
- **App Thinning**: the App Store delivers different builds for different devices. Unity supports this with Asset Catalogs and on-demand resources.
- **Privacy manifest**: starting in 2024, Apple requires a `PrivacyInfo.xcprivacy` file declaring data collection. Unity 6 includes a default; you must extend it for your specific data uses (analytics, advertising, etc.).
- **Tracking transparency**: if you use IDFA, you need the App Tracking Transparency prompt. Unity's `Application.RequestAdvertisingIdentifierAsync` returns a zeroed string until the user grants permission.
- **No interpreter fallback**: iOS does not allow interpreted code. IL2CPP is mandatory. The IL2CPP interpreter (used as a fallback for some platforms) is not available on iOS.

### 5.3 Build settings

In Unity's iOS Player Settings:
- **Scripting Backend**: IL2CPP (default).
- **Target Architecture**: ARM64 only.
- **Managed Stripping Level**: High (smallest build) or Medium (safer for reflection).
- **API Compatibility Level**: .NET Standard 2.1 (default in Unity 6).
- **iOS Deployment Target**: iOS 15.0+ for Unity 6.
- **Architecture**: ARM64 (no ARMv7).

### 5.4 iOS build pipeline

```bash
xcodebuild -project Unity-iPhone.xcodeproj \
  -scheme Unity-iPhone \
  -configuration Release \
  -archivePath build/MyApp.xcarchive \
  archive
```

This produces an `.xcarchive` for App Store Connect upload. For local testing, use Xcode's Devices window.

### 5.5 Common iOS issues

- **IL2CPP + generics + value types**: each unique value type instantiation must be AOT-compiled. If you use `List<MyStruct>`, the JIT compiler compiles a version for `MyStruct`. If `MyStruct` is only used via reflection, it might not be in the build. Symptom: works on simulator, crashes on device. Fix: explicit static reference.
- **App Store rejection for using private APIs**: Unity sometimes uses private APIs (esp. for graphics) that Apple rejects. Check the rejection message; Unity has workarounds in 6.x.
- **Bitcode**: deprecated in Xcode 14, removed in Xcode 15. Unity 6 does not produce bitcode.
- **Launch time**: iOS users are sensitive to launch time. Target < 2 seconds to first frame. Profile with Instruments on a real device, not simulator.

## 6. Android specifics

### 6.1 ARM64 only

Since 2019, Google Play requires 64-bit apps. Unity 6 with IL2CPP is ARM64 by default. Drop ARMv7.

### 6.2 Build targets

In Unity's Android Player Settings:
- **Scripting Backend**: IL2CPP.
- **Target Architectures**: ARM64.
- **Minimum API Level**: 24 (Android 7.0) for Unity 6.
- **Target API Level**: 34 (Android 14) for 2024 Play Store submissions.
- **Managed Stripping Level**: High.

### 6.3 .aab vs .apk

- **APK**: legacy Android package. Single file, contains all architectures and resources.
- **AAB (Android App Bundle)**: since 2021, the only upload format for new Play Store apps. AAB is processed by Play to produce per-device APKs.
- Unity 6 can build both. AAB is the default for "Build App Bundle" checked. The .aab is what you upload to Play Console.

AAB advantages:
- Smaller downloads (Play generates per-device splits).
- Dynamic feature delivery.
- Asset pack delivery (see below).

### 6.4 Play Asset Delivery

Play Asset Delivery (PAD) is Google's answer to on-demand resources. Unity supports it via the `com.google.android.appbundle` package and the Addressables build target "Play Asset Delivery."

PAD modes:
- **Install time**: included in the install, always available.
- **Fast follow**: downloaded right after install, in the background.
- **On demand**: downloaded when the game requests it.

The Addressables build pipeline produces an asset pack per group. You upload the AAB; Play extracts the asset packs to the user's device based on the mode.

PAD is a real win for large games. A 4 GB game that streams content can be a 200 MB install with 3.8 GB streamed.

### 6.5 Gradle and the build process

Unity 6 uses Gradle for Android builds. The Gradle template lives in `Assets/Plugins/Android/`. Unity invokes Gradle to produce the AAB. CI builds need the Android SDK and NDK installed and Unity's environment variables set.

```bash
$UNITY_PATH/Unity \
  -batchmode -quit -nographics \
  -projectPath $PROJECT_PATH \
  -buildTarget Android \
  -executeMethod BuildScript.BuildAndroid \
  -logFile build.log
```

The Android NDK version Unity expects is specific. Unity 6 expects NDK r25b or later. Mismatched NDK = linker errors that look like IL2CPP failures.

### 6.6 Android performance

Android devices span a massive range. Target the lowest-spec device in your supported list and design the game to scale up. The Pixel 4a is a common minimum-spec reference device.

- **GPU**: Adreno 640 (Pixel 4) is roughly the floor for mid-tier 3D games.
- **CPU**: Snapdragon 730G or equivalent.
- **RAM**: 4 GB.
- **Vulkan**: required for modern Android. Unity 6 uses Vulkan by default if the device supports it.

Profile on the lowest-spec device you support. If it runs at 30 fps there, it runs at 60 fps on flagships. The opposite is not true.

## 7. Console specifics

### 7.1 SDK requirements

Console development requires licensed SDKs from the platform holder. You cannot develop for PS5/Xbox/Switch without a registered developer account and an NDA-protected SDK.

- **PS5**: Sony's SDK is "PS5 SDK" distributed via the developer portal. Unity has a `com.unity.modules.ps5` module that requires the SDK to compile.
- **Xbox**: Microsoft's GDK (Game Development Kit) is the unified SDK for Xbox One, Xbox Series S, Xbox Series X. Unity's `com.unity.modules.xboxone` and `com.unity.modules.gdk` are the integration points.
- **Switch**: Nintendo's SDK is "NintendoSDK" distributed via the developer portal. Unity's `com.unity.modules.switch` requires the SDK.

You cannot develop for consoles on a stock Unity install. The platform modules only compile when the SDK is detected.

### 7.2 TRC/TCR

- **TRC (Technical Requirements Checklist)**: Sony's certification requirements. Covers everything from button response time to save data integrity.
- **TCR (Technical Certification Requirements)**: Microsoft's equivalent. Less prescriptive, more "your game must work" oriented.
- **Lotcheck (Nintendo)**: Nintendo's certification. Strict.

Common reasons for failure:
- Suspend/resume: the game must handle a system-level suspend (power button on Switch, dashboard on Xbox) and resume within seconds. Lose state, fail.
- Save data integrity: a power loss during save must not corrupt the save. Use atomic save patterns.
- First-frame: the first user-visible frame must appear within X seconds. Profile launch time on the actual dev kit.
- Error handling: a thrown exception during gameplay must not crash the game. Catch and recover.
- Memory budgets: hitting the memory ceiling at any point (including shader compilation spikes) fails certification.

### 7.3 Memory budgets

Console certification requires a memory budget report. You must declare peak memory usage and stay under it.

- **PS5**: 12.8 GB shared GDDR6 (system uses ~2.5 GB, leaves ~10 GB for the game). Track in the profiler.
- **Xbox Series S**: 8 GB shared GDDR6 (~2 GB for system, ~6 GB for game). Series S is the lowest-spec current-gen console; design for it.
- **Xbox Series X**: 13.5 GB GDDR6.
- **Switch**: 4 GB LPDDR4 shared. The system uses 1.5-2 GB, leaves ~2 GB for the game. Switch is the most memory-constrained current platform.

Memory profiler module 12 covers this. The key is: know your peak, profile on the actual dev kit, and have a regression test in CI.

### 7.4 Screenshot mode

Console certification requires a screenshot/video capture mode. The platform APIs (PS5's `sceScreenShotSetCaptureImage` etc.) let the platform capture gameplay. The game must:
- Disable HUD or use a "clean HUD" mode.
- Disable pause UI.
- Run at the certification-required resolution and framerate.
- Render the splash screen on demand.

```csharp
public class ScreenshotMode : MonoBehaviour
{
    public static bool IsActive { get; private set; }

    void OnEnable()
    {
#if UNITY_PS5 || UNITY_GAMECORE || UNITY_SWITCH
        Application.platformHooks?.OnScreenshotRequest += HandleScreenshot;
#endif
    }

    void OnDisable()
    {
#if UNITY_PS5 || UNITY_GAMECORE || UNITY_SWITCH
        Application.platformHooks?.OnScreenshotRequest -= HandleScreenshot;
#endif
    }

    void HandleScreenshot()
    {
        IsActive = true;
        // hide HUD, freeze simulation, render clean frame
    }
}
```

The hook is platform-specific. Use `#if` directives to gate.

## 8. Real-device testing

The senior rule: **test on real devices from day one**. The editor is not the platform.

- **iOS simulator**: not a real device. The simulator uses an x86 Mac CPU; the device uses ARM. Graphics drivers are different. Performance is different. Use it for fast iteration; do not ship-test on it.
- **Android emulator**: closer to a real device, but the GPU is emulated. Vulkan behavior differs. Use a real device for graphics testing.
- **Console dev kit**: required for certification. Cannot be replaced by anything else. Profile on the dev kit, not on PC.

CI runners that build for mobile/console should be matched to the platform. A Linux CI server cannot build for iOS. A Mac CI server can build for iOS but cannot test on a device (no device attached). Real device farms exist (SauceLabs, BrowserStack, AWS Device Farm) for automated testing.

## 9. Target the lowest-spec device

Senior planning rule: pick the lowest-spec device you intend to support, profile on that device, and design the game to scale up from there. A 2020 mid-tier Android is the floor for most AAA-style Unity games. A 2018 iPhone is the floor for iOS.

- The lowest-spec device defines your base asset quality, draw call budget, and shader complexity.
- Flagship devices are tested for "does it run at 60 fps" — not for "does it work."
- Mid-tier devices are tested for "does it run at 30 fps with the base asset set."
- Low-tier devices are tested for "does it boot, does it not crash, does the core gameplay loop function."

You cannot ship a 60 fps experience for the latest iPhone and a 30 fps experience for an old Android from the same binary without major engineering work. Plan for the floor.

## 10. Plan for IL2CPP from day one

If you start with Mono in the editor and switch to IL2CPP at the end of the project, you will discover that:
- Reflection-based JSON deserialization breaks (types stripped).
- Generic value-type collections break (AOT instantiation missing).
- Some third-party packages break (their link.xml is incomplete).
- Build time becomes a project risk (60-minute builds).

Plan for IL2CPP from the start:
- Build with IL2CPP in CI on every commit.
- Use explicit `[Preserve]` attributes on reflection-touched types.
- Maintain a `link.xml` that grows with the project.
- Test on a real iOS device in week 1, not week 50.

## 11. Common pitfalls

- **Reflection-based JSON deserialization** in production code: works in editor, crashes on device. Use `JsonUtility` (which is AOT-friendly) or write static serializers.
- **Generic value types with reflection**: `MyClass<MyStruct>` accessed only via reflection may not be AOT-compiled. Use a static reference.
- **Build time creep**: 20-minute builds in week 1 become 60-minute builds in week 20. Cache aggressively in CI.
- **App size growth**: 50 MB in week 1 becomes 500 MB in week 20. Profile assets. Use Addressables and streaming.
- **TestFlight / Play Console**: submitting for the first time reveals configuration issues (missing icons, wrong bundle ID, missing privacy manifest). Submit a build in week 1, even if it's empty, to validate the pipeline.
- **Privacy manifest**: iOS apps without a complete `PrivacyInfo.xcprivacy` are rejected. Add it in week 1.
- **Memory budget overcommit**: certification failure on console because peak memory exceeded the declared budget. Profile early and often.

## What to read next

- Module 12: profile on real devices, especially the lowest-spec target.
- Module 13: build pipeline for iOS, Android, and headless server.
- Module 8 (from the previous course): Addressables streaming and Play Asset Delivery.
- Module 14: the asset pipeline benefits from platform-aware preloading.

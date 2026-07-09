# Lab 11: Build, Strip, and Diagnose a Real Mobile Project

**Time**: 75 minutes
**Goal**: Build a Unity 6 project for iOS and Android, configure stripping, write a link.xml, hit the "works in editor, fails on build" trap, diagnose it, and fix it.

## Setup (5 min)

1. New Unity 6 project.
2. Install `com.unity.addressables` (covered in module 8 of the previous course).
3. Create three scenes: `Boot`, `Menu`, `Game`.
4. Create a `PlayerData` script with a JSON-serializable structure, and an `Inventory` script that uses reflection to load items from JSON.

`PlayerData.cs`:
```csharp
using System;
using System.Collections.Generic;
using UnityEngine;

[Serializable]
public class PlayerData
{
    public string Name;
    public int Level;
    public List<string> Inventory;
}
```

`ItemBase.cs`:
```csharp
using UnityEngine;

public abstract class ItemBase
{
    public abstract string DisplayName { get; }
    public abstract void Use(GameObject user);
}

public class HealthPotion : ItemBase
{
    public override string DisplayName => "Health Potion";
    public override void Use(GameObject user) { /* heal */ }
}

public class ManaPotion : ItemBase
{
    public override string DisplayName => "Mana Potion";
    public override void Use(GameObject user) { /* restore mana */ }
}
```

## Part A: Reflection-based inventory loader (15 min)

`InventoryLoader.cs`:
```csharp
using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;

public static class InventoryLoader
{
    public static List<ItemBase> LoadFromJson(string json)
    {
        var wrapper = JsonUtility.FromJson<ItemWrapper>(json);
        var result = new List<ItemBase>();
        var asm = typeof(ItemBase).Assembly;
        foreach (var typeName in wrapper.ItemTypes)
        {
            var type = asm.GetType(typeName);  // REFLECTION - will break with IL2CPP stripping
            if (type == null) throw new Exception($"unknown item type: {typeName}");
            result.Add((ItemBase)Activator.CreateInstance(type));
        }
        return result;
    }

    [Serializable]
    class ItemWrapper
    {
        public List<string> ItemTypes;
    }
}
```

`Main.cs`:
```csharp
using UnityEngine;

public class Main : MonoBehaviour
{
    void Start()
    {
        var items = InventoryLoader.LoadFromJson("{\"ItemTypes\":[\"HealthPotion\",\"ManaPotion\"]}");
        foreach (var item in items) Debug.Log($"loaded: {item.DisplayName}");
    }
}
```

## Part B: Build for iOS and observe the crash (15 min)

1. Switch build target to iOS.
2. Set Scripting Backend = IL2CPP, Target Architecture = ARM64, Managed Stripping = High.
3. Build to a folder. Open in Xcode, deploy to a device or simulator.
4. Launch the app. Observe: editor logs "loaded: Health Potion" and "loaded: Mana Potion". iOS build crashes or logs "unknown item type: HealthPotion".

This is the stripping bug. The reflection call to `asm.GetType("HealthPotion")` returns null because the HealthPotion type was stripped from the managed binary. The editor doesn't strip (Mono JIT loads everything), so it works in the editor.

## Part C: Fix with link.xml (15 min)

Create `Assets/link.xml`:
```xml
<linker>
  <assembly fullname="Assembly-CSharp">
    <type fullname="HealthPotion" preserve="all"/>
    <type fullname="ManaPotion" preserve="all"/>
  </assembly>
</linker>
```

Rebuild. Deploy. The items now load.

The senior version of the fix is `[Preserve]` attributes:
```csharp
using UnityEngine.Scripting;

[Preserve]
public class HealthPotion : ItemBase { /* ... */ }

[Preserve]
public class ManaPotion : ItemBase { /* ... */ }
```

`[Preserve]` is per-type, link.xml is per-assembly. Use both. The attribute is harder to miss in code review.

## Part D: Build for Android and configure ARM64 (15 min)

1. Switch build target to Android.
2. Set Scripting Backend = IL2CPP, Target Architecture = ARM64 (uncheck ARMv7 if visible).
3. Set Minimum API Level = 24, Target API Level = 34.
4. Set Managed Stripping = High.
5. Build AAB. Upload to Play Console internal testing track. Install on a real device.
6. Observe: app launches, items load, gameplay works.

## Part E: Configure Addressables for mobile streaming (10 min)

Set Addressables build target to Android or iOS. Build the player content. Update `RemoteBuildPath` and `LocalBuildPath` for the platform. Verify the streaming assets folder contains the bundles.

## Verification

1. Editor: items load, logs are visible.
2. iOS device: items load, no `MissingMethodException`, no `TypeLoadException`.
3. Android device: same.
4. Build size: under 50 MB for the bare project. Add some test assets and observe growth.
5. IL2CPP build time: 2-5 minutes for a small project. This scales linearly with managed code size.
6. Link.xml in the build: the iOS .ipa contains a stripped binary; the link.xml does not appear in the build (it's a build-time input).

## Common pitfalls

- **Forgetting to test on a real device** before milestone 5. The simulator hides 80% of the bugs. TestFlight/Play Internal Testing in week 1.
- **Stripping level set to Low for "just in case"**: this hides stripping bugs until release. Use High in development; the bugs are the same as production.
- **AOT generic instantiation missing**: if you have `List<MyStruct>` accessed only via reflection, the AOT compiler may not generate the instantiation. Use a static reference (`var _ = new List<MyStruct>();` at startup) to force AOT compilation.
- **Build size doubled after adding a single asset**: usually a texture with mipmaps that wasn't compressed. Check the texture importer settings.
- **App Store rejection for missing privacy manifest**: add `Assets/Plugins/iOS/PrivacyInfo.xcprivacy` early.
- **Gradle version mismatch**: Unity 6 requires a specific Gradle version. If your Android SDK has a different Gradle, the build fails with cryptic errors. Use the Unity Hub to install the recommended Gradle.

## What we're testing

- Can you build a Unity project for iOS and Android with IL2CPP?
- Do you understand what managed code stripping does and why it breaks reflection?
- Can you write a link.xml and use `[Preserve]` attributes?
- Can you read IL2CPP build logs to find what was stripped?
- Do you know the target architecture and API level for iOS and Android in Unity 6?

## Stretch goals

- Profile the iOS build in Instruments (Xcode). Find the largest stack frame in the launch sequence.
- Configure Play Asset Delivery for a large asset group. Verify the AAB has split asset packs.
- Build the same project for WebGL. Observe the differences in scripting backend and stripping.
- Test the build on a low-end Android device (Pixel 4a equivalent). Measure frame time. If it's over 16 ms (60 fps), identify the bottleneck with the Profiler.

# 07 — Asset Pipeline & Addressables

Module 2 was about runtime memory; this module is about **build size,
content updates, and the asset pipeline that bridges them**. The senior
default in 2026 is **Addressables**, with three reasons:

1. **Asynchronous loading.** Frame hitches from sync loads are the
   #2 cause of "the game stutters" after GC.
2. **Content updates.** Ship a 200 MB download + 50 MB patch instead
   of a 250 MB re-download.
3. **Memory awareness.** You can load and unload groups of assets
   together, with reference counting.

`Resources/` is fine for prototypes. It's wrong for shipping.

---

## 1. The three ways to load an asset in Unity

```csharp
// 1. Direct reference (drag-and-drop in inspector)
public GameObject playerPrefab;
// Loaded with the scene. Always in memory. No way to unload.

// 2. Resources.Load (the old way)
var prefab = Resources.Load<GameObject>("Player");
// All Resources/ assets ship in the build. Cannot be unloaded
// individually. Cannot do content updates. Senior rule: no.

// 3. Addressables.LoadAssetAsync (the senior way)
var handle = Addressables.LoadAssetAsync<GameObject>("Player");
await handle.Task;
var prefab = handle.Result;
// Async, ref-counted, can be unloaded, content-update friendly.
```

The transition from `Resources` to `Addressables` is the single most
common senior migration.

---

## 2. The Addressables mental model

Three concepts:

| Concept | What |
|---------|------|
| **Address** | A string (or hash) that names a single asset or group. |
| **Group** | A collection of assets that ship and load together. |
| **Label** | A string tag on an asset. Multiple labels per asset. |

The mental model is "labels are like a database query; groups are like
folders that get packed together; addresses are unique keys".

```csharp
// Load by address
var handle = Addressables.LoadAssetAsync<Sprite>("ui/icons/sword");

// Load by label (all assets tagged "Level1")
var handles = Addressables.LoadAssetsAsync<Sprite>("Level1", sprite => { });

// Release
Addressables.Release(handle);
```

`Addressables.Release` is the equivalent of `Dispose` for native
arrays. The reference count decrements; when it hits 0, the asset
unloads. **Forgetting to release is the senior bug.**

---

## 3. Setup

1. **Window → Package Manager → search "Addressables" → Install**.
2. **Window → Asset Management → Addressables → Groups**.
3. The first time, click **Create Addressables Settings**. Unity
   creates:
   - `Assets/AddressableAssetsData/`
   - A default group called "Built In Data" (don't put your stuff
     there).
4. Select assets in the Project window; in the inspector, check
   **Addressable**. Assign an address and any labels.

**The senior default**: assets go in **groups by use case**, not
by folder:

- `Levels` (label "Level1", "Level2", ...)
- `UI` (label "HUD", "Menus")
- `Audio` (label "Music", "SFX")
- `Characters` (label "Player", "NPCs", "Enemies")
- `Cinematics` (label "Cutscene1", "Cutscene2")

---

## 4. Async loading patterns

### 4.1 The naive way (don't do this)

```csharp
async void Start()
{
    var prefab = await Addressables.LoadAssetAsync<GameObject>("Player").Task;
    Instantiate(prefab);   // wrong: async void hides exceptions
}
```

### 4.2 The right way: `Awaitable` (Unity 2023+)

```csharp
async Awaitable Start()
{
    var handle = Addressables.LoadAssetAsync<GameObject>("Player");
    await handle;       // Awaitable supports AsyncOperationHandle directly
    Instantiate(handle.Result);
}
```

### 4.3 The right way: a wrapper

```csharp
public static class AssetLoader
{
    public static async Awaitable<T> LoadAsync<T>(string address) where T : Object
    {
        var handle = Addressables.LoadAssetAsync<T>(address);
        await handle;
        if (handle.Status != AsyncOperationStatus.Succeeded)
        {
            throw new Exception($"Addressables load failed: {address}");
        }
        return handle.Result;
    }

    public static void Release<T>(T asset) where T : Object
    {
        Addressables.Release(asset);
    }
}
```

---

## 5. Reference counting: the part that bites

Addressables uses **reference counting** internally. Every
`LoadAssetAsync` increments a ref. Every `Release` decrements. When
the count hits 0, the asset unloads. The "**asymmetric load/release**"
is the most common bug.

```csharp
// 5 LoadAssetAsync calls
var h1 = Addressables.LoadAssetAsync<Sprite>("A");
var h2 = Addressables.LoadAssetAsync<Sprite>("A");
var h3 = Addressables.LoadAssetAsync<Sprite>("A");
var h4 = Addressables.LoadAssetAsync<Sprite>("A");
var h5 = Addressables.LoadAssetAsync<Sprite>("A");

// 4 Release calls — asset is STILL loaded (ref count 1)
Addressables.Release(h1);
Addressables.Release(h2);
Addressables.Release(h3);
Addressables.Release(h4);
```

**Senior pattern**: track handles in a field, release in pairs.

```csharp
public class LevelLoader : MonoBehaviour
{
    AsyncOperationHandle<Sprite> _iconHandle;
    AsyncOperationHandle<GameObject> _enemyHandle;

    async Awaitable LoadLevelAsync(string level)
    {
        _iconHandle = Addressables.LoadAssetAsync<Sprite>($"ui/{level}/icon");
        _enemyHandle = Addressables.LoadAssetAsync<GameObject>($"levels/{level}/enemy");
        await _iconHandle;
        await _enemyHandle;
    }

    void OnDestroy()
    {
        if (_iconHandle.IsValid()) Addressables.Release(_iconHandle);
        if (_enemyHandle.IsValid()) Addressables.Release(_enemyHandle);
    }
}
```

---

## 6. Content updates: ship a patch, not a re-download

The killer feature of Addressables is **content catalogs**. The
build has:

- `catalog_1.0.0.json`: which assets exist and where to find them
- `bundle_*.bundle`: the actual data

When you update the game:

1. You rebuild the **content catalog** (a JSON file) with the
   changed/new assets.
2. You upload only the **changed bundles** to a CDN.
3. On launch, the player downloads the new catalog (small),
   downloads the **changed** bundles, and the rest of the game is
   unchanged.

**Result**: a 50 MB content update instead of a 250 MB re-download.
**Required**: a CDN, a server that can serve the catalog.

For the setup:

1. **Window → Asset Management → Addressables → Groups**.
2. In the group's inspector, set **Build Path** to a remote URL.
3. **Build → New Build → Default Build Script** produces the bundles
   + catalog.
4. Upload to your CDN.

This is why every shipping Unity game in 2026 uses Addressables.

---

## 7. Memory: how Addressables interacts with the budget

Addressables does **not** automatically bound its memory. It will
load what you tell it to load, and keep it loaded until you
release. The senior discipline:

- **No "load everything on startup"**. The classic rookie mistake.
- **No "load on first use, never release"**. The classic mid-level
  mistake.
- **Yes "load on level entry, release on level exit"**. The senior
  pattern.

```csharp
public class LevelController : MonoBehaviour
{
    AsyncOperationHandle<SceneInstance> _sceneHandle;

    public async Awaitable LoadLevelAsync(string address)
    {
        if (_sceneHandle.IsValid()) await UnloadCurrentAsync();
        _sceneHandle = Addressables.LoadSceneAsync(address, LoadSceneMode.Additive);
        await _sceneHandle;
    }

    public async Awaitable UnloadCurrentAsync()
    {
        if (!_sceneHandle.IsValid()) return;
        await Addressables.UnloadSceneAsync(_sceneHandle);
    }
}
```

---

## 8. Build size: the texture rule (continued from module 6)

A typical mobile Unity game's build size:

```
APK / IPA total:   250 MB
├── Managed code:   30 MB   ← IL2CPP, partially stripped
├── Native engine:  40 MB
├── Assets
│   ├── Textures:   150 MB  ← biggest controllable
│   ├── Meshes:     10 MB
│   ├── Audio:      20 MB
│   └── Shaders:    5 MB
└── Engine libs:    5 MB
```

The senior fix:

1. **Textures** — verify compression, max size, mipmaps. Use Crunch
   on non-hot assets.
2. **Audio** — convert to Vorbis (.ogg) for music, ADPCM for SFX.
   22050 Hz for SFX, 44100 for music.
3. **Meshes** — enable mesh compression in import settings.
4. **Shaders** — strip unused variants (`Shader Variant Collection`).
5. **Managed code** — `Managed Stripping Level = High` (or
   `Medium` if you use reflection).

### Managed code stripping, the "why my game crashes on iOS" rule

`Managed Stripping Level` removes unused managed code from the build.
This is **necessary** for iOS (the build won't ship otherwise). The
levels:

- **Low**: only removes obvious dead code. Safe. Build is large.
- **Medium**: removes more. Mostly safe. The right default.
- **High**: aggressive. **Breaks reflection-based code** (JsonUtility,
  some plugins, some Unity APIs).

**The senior workflow**:

1. Set `High` for the final build.
2. If the game crashes on launch, the cause is a stripped method
   that was called via reflection.
3. Add to `link.xml` to preserve the assembly:
   ```xml
   <linker>
     <assembly fullname="MyAssembly" preserve="all"/>
   </linker>
   ```
4. Repeat.

`link.xml` is in `Assets/link.xml`. **Module 10 has a worked
example for iOS specifically.**

---

## 9. The Build Report (the document you actually read)

After a build, open `Edit → Preferences → Build Report`, or find
`Build/Reports/BuildReport.json` in your project after a build.

The report has:

- **Total build size** and per-platform breakdown.
- **Asset compression** time.
- **Managed code stripping**: how much was removed.
- **Shader variants**: how many compiled.
- **Texture size** in the final build.

The senior weekly review: track total build size over time. If it
jumps 20 MB, find why.

---

## 10. Build settings that bite

| Setting | Where | Senior choice |
|---------|-------|---------------|
| Scripting Backend | Player Settings → Other Settings | IL2CPP for release, Mono for editor iteration |
| Api Compatibility Level | Player Settings → Other Settings | .NET Standard 2.1 (broadest) |
| Managed Stripping Level | Player Settings → Other Settings | High for release |
| Compression | Player Settings → Publishing Settings | LZ4 for development, LZ4HC for release |
| Texture compression override | Player Settings → Other Settings | ASTC for mobile, BC7 for PC |
| Target Architectures | Player Settings → Other Settings | **ARM64 only** for mobile (32-bit is dead) |
| IL2CPP Code Generation | Player Settings → Other Settings | Faster runtime / Faster build (pick per project) |

The Texture Compression Override is **the most underused setting**.
Unity 6 can build an APK with ASTC textures without needing a
second build. You can ship one build that uses GPU-appropriate
compression.

---

## 11. The senior anti-patterns

- **Loading all assets at startup.** "Preload everything" is the
  classic answer to the wrong question. Use Addressables to load on
  demand.
- **Using `Resources.Load` in shipping code.** Editor-only is OK.
- **Ignoring `Release`.** The ref count never hits zero; the asset
  stays in memory forever.
- **Loading the same asset via two different addresses.** Each load
  is a ref count; releasing one doesn't free it.
- **Putting large assets in `Resources/`.** They ship in the
  initial download with no content update path.
- **Not using `link.xml`** when you have reflection-based code. The
  iOS build crashes at launch with `MissingMethodException`.

---

## Summary

- Addressables is the senior default. Resources is the prototype
  default.
- Labels for queries, groups for packaging, addresses for unique
  keys.
- Async loading with `Awaitable`. Never `async void`.
- Reference counting: track your handles, release in pairs.
- Content updates: catalog + bundles + CDN. 50 MB patch beats
  250 MB re-download.
- Build size: textures dominate; compression, max size, mipmaps.
- Managed stripping: `High` for release, `link.xml` for reflection.
- Read the Build Report. Track size over time.
- No "load everything at startup". No `Resources.Load` in shipping
  code.

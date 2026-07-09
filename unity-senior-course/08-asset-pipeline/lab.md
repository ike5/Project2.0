# Lab 08 — Addressables: Async Loading and Content Updates

A hands-on session with Addressables. By the end you will have
Addressables configured, an asset loaded async, and a basic
content update flow.

**Time**: 90 minutes.

**Prerequisite**: Addressables package installed.

---

## Step 1 — Install and configure

1. **Window → Package Manager → search "Addressables" → Install**.
2. **Window → Asset Management → Addressables → Groups**.
3. Click **Create Addressables Settings**.

The first time, Unity creates:

- `Assets/AddressableAssetsData/`
- A default "Built In Data" group.

## Step 2 — Mark assets as addressable

1. Create a `Prefabs/Enemy.prefab` (a cube with a `Health`
   component).
2. Select the prefab in the Project window.
3. In the inspector, ☑ **Addressable**.
4. Set the address to `Enemy`.

The prefab now has an address. Anything in your code can load
it by that name.

## Step 3 — A simple async loader

Create `Assets/Scripts/Assets/EnemyLoader.cs`:

```csharp
using System;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace MyGame.Assets
{
    public class EnemyLoader : MonoBehaviour
    {
        [SerializeField] string _address = "Enemy";
        AsyncOperationHandle<GameObject> _handle;

        async void Start()
        {
            try
            {
                _handle = Addressables.LoadAssetAsync<GameObject>(_address);
                await _handle;
                if (_handle.Status != AsyncOperationStatus.Succeeded)
                {
                    Debug.LogError($"Failed to load {_address}");
                    return;
                }
                Debug.Log($"Loaded {_address}: {_handle.Result.name}");
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }
        }

        void OnDestroy()
        {
            if (_handle.IsValid()) Addressables.Release(_handle);
        }
    }
}
```

The `await` uses Unity's `AsyncOperationHandle.GetAwaiter()`,
which yields until the load is complete. **This is the
right pattern for async Addressables in 2026.**

## Step 4 — A label-based loader

1. Select the `Enemy` prefab in the Project window.
2. In the inspector, in the Addressable section, click +
   under **Labels** and add `Level1`.
3. Add a second prefab, mark it Addressable, label it
   `Level1` with address `Bullet`.
4. Create a `Level1Loader.cs`:

```csharp
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

public class Level1Loader : MonoBehaviour
{
    readonly List<AsyncOperationHandle> _handles = new();

    async void Start()
    {
        var op = Addressables.LoadAssetsAsync<Object>("Level1", asset =>
        {
            Debug.Log($"Loaded: {asset.name}");
        });
        _handles.Add(op);
        await op;
    }

    void OnDestroy()
    {
        foreach (var h in _handles)
            if (h.IsValid()) Addressables.Release(h);
        _handles.Clear();
    }
}
```

Run. Both prefabs load.

## Step 5 — Reference counting

Add this to a test:

```csharp
var h1 = Addressables.LoadAssetAsync<Sprite>("Icon");
var h2 = Addressables.LoadAssetAsync<Sprite>("Icon");
var h3 = Addressables.LoadAssetAsync<Sprite>("Icon");
Addressables.Release(h1);
Addressables.Release(h2);
Addressables.Release(h3);
// Asset is now unloaded
```

Verify with the Memory Profiler: the texture appears during
the load, disappears after the third `Release`.

## Step 6 — A scene-loaded additively via Addressables

```csharp
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.ResourceProviders;
using UnityEngine.SceneManagement;

public class SceneLoader : MonoBehaviour
{
    AsyncOperationHandle<SceneInstance> _handle;

    public async void LoadLevelAsync(string address)
    {
        if (_handle.IsValid())
        {
            await Addressables.UnloadSceneAsync(_handle);
        }
        _handle = Addressables.LoadSceneAsync(address, LoadSceneMode.Additive);
        await _handle;
    }

    void OnDestroy()
    {
        if (_handle.IsValid()) Addressables.Release(_handle);
    }
}
```

`SceneInstance` is a wrapper around a `Scene` that Addressables
manages. Calling `UnloadSceneAsync(handle)` unloads the scene
and decrements the ref count.

## Step 7 — Build the player content

1. **Window → Asset Management → Addressables → Groups**.
2. Click **Build → New Build → Default Build Script**.
3. Unity creates:
   - `Library/com.unity.addressables/aa/...` (or similar)
     — the addressable bundles.
   - `ServerData/...` — for local testing.

The bundles contain your asset data; the catalog describes
what's in them.

## Step 8 — Local content update

1. Open the `Enemy` prefab. Change the cube's color to red.
   Save.
2. **Window → Asset Management → Addressables → Groups → Build
   → Update Previous Build**.

Unity rebuilds **only the changed bundles** and updates the
catalog. The unchanged bundles are untouched.

This is the content-update flow in action: ship a 5 MB
"redesigned enemy" patch instead of a 250 MB re-download.

## Step 9 — Verify with the Memory Profiler

1. Open Memory Profiler.
2. Load the level via Addressables.
3. Snapshot.
4. Unload the level.
5. Snapshot.
6. Diff.

The diff should show the loaded assets in snapshot 3, and
gone in snapshot 5. **The ref count is working.**

## Stretch goals

- **CDN setup**: configure the build to upload to a remote
  URL. (AWS S3, Cloudflare R2, or your own server.)
- **Custom build script**: write an `IAddressableAssetBuildStrategy`
  that does custom chunking.
- **Async loading UI**: a loading screen that uses
  `AsyncOperationHandle.PercentComplete` to drive a progress
  bar.

---

## What you should now understand

- Addressables is the senior default. `Resources` is the
  prototype default.
- The pattern: `LoadAssetAsync` → `await` → use → `Release`.
- Reference counting: track your handles, release in pairs.
- Content updates: the catalog + bundles model. Ship patches,
  not re-downloads.
- The Memory Profiler is the verification tool.

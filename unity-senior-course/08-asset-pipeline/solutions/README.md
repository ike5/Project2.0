# Solutions 08 — Content Update Pipeline

---

## The senior profile setup

`Assets/AddressableAssetsData/AddressableAssetSettings.asset`
should have a "Remote" profile:

| Variable | Local | Remote |
|----------|-------|--------|
| Local.BuildPath | Library/com.unity.addressables/aa/ | (same) |
| Local.LoadPath | {UnityEngine.Application.streamingAssetsPath}/aa | (same) |
| Remote.BuildPath | ServerData/[BuildTarget] | (same) |
| Remote.LoadPath | http://localhost:8000/[BuildTarget] | (same) |

Switch the active profile with the dropdown in the Groups
window.

## The senior loader

```csharp
using System;
using System.Threading;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace MyGame.Assets
{
    public class RemoteAssetLoader : MonoBehaviour
    {
        AsyncOperationHandle _initHandle;
        CancellationTokenSource _cts;

        async void Start()
        {
            _cts = new CancellationTokenSource();
            try
            {
                _initHandle = Addressables.InitializeAsync(false);
                await _initHandle;

                Debug.Log($"[Addressables] Loaded from: {Addressables.RuntimePath}");

                await CheckForUpdatesAsync(_cts.Token);
                await PreloadAsync(_cts.Token);
            }
            catch (OperationCanceledException)
            {
                // expected on quit
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }
        }

        async Awaitable CheckForUpdatesAsync(CancellationToken ct)
        {
            var checkHandle = Addressables.CheckForCatalogUpdates(false);
            try
            {
                await checkHandle;
                if (checkHandle.Status != AsyncOperationStatus.Succeeded) return;
                if (checkHandle.Result == null || checkHandle.Result.Count == 0) return;

                Debug.Log($"[Addressables] Found {checkHandle.Result.Count} catalog update(s)");
                var updateHandle = Addressables.UpdateCatalogs(checkHandle.Result, false);
                await updateHandle;
                if (updateHandle.IsValid()) Addressables.Release(updateHandle);
            }
            finally
            {
                if (checkHandle.IsValid()) Addressables.Release(checkHandle);
            }
        }

        async Awaitable PreloadAsync(CancellationToken ct)
        {
            // Pre-download a label
            var dlHandle = Addressables.DownloadDependenciesAsync("Level1", false);
            while (!dlHandle.IsDone)
            {
                ct.ThrowIfCancellationRequested();
                Debug.Log($"[Addressables] Downloading: {dlHandle.PercentComplete:P0}");
                await Awaitable.NextFrameAsync(ct);
            }
            if (dlHandle.Status == AsyncOperationStatus.Failed)
                Debug.LogError("[Addressables] Download failed");
            if (dlHandle.IsValid()) Addressables.Release(dlHandle);
        }

        void OnDestroy()
        {
            _cts?.Cancel();
            _cts?.Dispose();
            if (_initHandle.IsValid()) Addressables.Release(_initHandle);
        }
    }
}
```

## The patch workflow

```bash
# 1. Build initial
unity -batchmode -projectPath . -executeMethod AddressablesBuilder.Build

# 2. Modify a character prefab

# 3. Build update
unity -batchmode -projectPath . -executeMethod AddressablesBuilder.Update

# 4. Diff
du -sh ServerData/StandaloneLinux64/
find ServerData/StandaloneLinux64/ -newer /tmp/build-marker -ls
# expect: only the changed bundle is "newer"
```

The senior verification:

- A 1-character change = 1 bundle, typically < 5 MB.
- A texture change = 1 bundle, sized like the texture.
- A scene change = 1 bundle, sized like the scene.
- A code change = the player binary (different from
  Addressables).

## Common pitfalls

- **Build path and load path don't match**. The player can't
  find the bundles. Verify in
  `AddressableAssetSettings.RemoteLoadPath`.
- **Catalog hasn't been updated**. After a content change,
  you must rebuild the catalog. **Build → Update Previous
  Build** does this.
- **Forgetting to release the catalog update handle**. Leaks
  the new catalog in memory.
- **Local URL hardcoded in shipping build**. Use a build
  script that sets the URL based on the build target.
- **No version field in the catalog**. Without versioning,
  you can't roll back a bad update.

## The senior rules

1. **Addressables is the senior default.** Resources is the
   prototype default.
2. **Track handles, release in pairs.** Ref count = 0 means
   unload.
3. **Catalog updates at startup.** 1 small JSON, maybe a
   few bundles.
4. **Pre-download non-critical content.** The player doesn't
   need the level 3 textures at level 1.
5. **Always set the `RemoteLoadPath` per profile.** Don't
   hardcode URLs.

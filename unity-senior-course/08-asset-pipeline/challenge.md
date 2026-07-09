# Challenge 08 — Build a Content Update Pipeline

A studio wants to ship a 200 MB initial download and 5–20 MB
content patches. Your job: stand up the Addressables pipeline
with a remote catalog, build a test scene, simulate an update,
and verify the patch is small.

**Time**: 3 hours.

---

## Requirements

- 1 Addressables group per content type (UI, Levels, Audio,
  Characters).
- A "build to local" path for development.
- A "build to remote" path with a fake CDN (a local HTTP
  server, e.g. `python -m http.server`).
- A loader that fetches the catalog from the remote URL at
  startup.
- A test that proves a 1-character change ships as a < 5 MB
  patch.

## Setup

1. **Window → Asset Management → Addressables → Groups →
   Profile → Manage Profiles**.
2. Add a new profile "Remote":
   - Local Build Path: `Library/com.unity.addressables/aa/`
   - Local Load Path: same.
   - Remote Build Path: `ServerData/[BuildTarget]`
   - Remote Load Path: `http://localhost:8000/[BuildTarget]`

3. For each group, set Build & Load Paths to "Remote".

4. Add assets to each group with descriptive addresses.

5. **Build → New Build → Default Build Script**. The output
   goes to `ServerData/StandaloneLinux64/` (or your build
   target).

6. Run a local HTTP server in `ServerData/`:

   ```bash
   cd ServerData
   python3 -m http.server 8000
   ```

7. In a built player, the catalog loads from
   `http://localhost:8000/.../catalog_1.0.0.json`.

## Verify the patch

1. Build the initial content. Note the size of
   `ServerData/StandaloneLinux64/`.
2. Change one character prefab.
3. **Build → Update Previous Build**.
4. Note the size of the *changed* bundle.
5. The unchanged bundles should not have been rewritten.
   `git status` or `find ... -newer ...` should show only
   the changed bundle.

**Expected**: a single bundle of < 5 MB is updated; the rest
of the catalog is unchanged.

## The senior loader

```csharp
using System;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

public class RemoteAssetLoader : MonoBehaviour
{
    AsyncOperationHandle _catalogHandle;

    async void Start()
    {
        try
        {
            _catalogHandle = Addressables.InitializeAsync();
            await _catalogHandle;
            Debug.Log("Catalog initialized from " + Addressables.RuntimePath);

            // Check for updates
            var checkHandle = Addressables.CheckForCatalogUpdates(false);
            await checkHandle;
            if (checkHandle.Result.Count > 0)
            {
                Debug.Log("Updates available: " + checkHandle.Result.Count);
                var updateHandle = Addressables.UpdateCatalogs(checkHandle.Result, false);
                await updateHandle;
                Addressables.Release(updateHandle);
            }
            Addressables.Release(checkHandle);

            // Load assets as usual
            var enemyHandle = Addressables.LoadAssetAsync<GameObject>("Enemy");
            await enemyHandle;
            // ...
        }
        catch (Exception e)
        {
            Debug.LogException(e);
        }
    }
}
```

The pattern:

1. `InitializeAsync()` — load the catalog from the remote URL.
2. `CheckForCatalogUpdates` — see if a newer catalog is
   available.
3. `UpdateCatalogs` — download the new catalog.
4. `LoadAssetAsync` — load from the (possibly updated) catalog.

## What we're testing

- You can stand up the Addressables pipeline with a local CDN.
- You can ship a small content patch.
- The senior loader handles catalog updates gracefully.
- The Memory Profiler shows the new assets, not the old.

## Stretch

- **Custom IResourceProvider**: write a custom provider that
  fetches from a memory cache.
- **Async loading UI**: a loading screen that shows the catalog
  download progress.
- **Pre-download**: use `Addressables.DownloadDependenciesAsync`
  to pre-fetch assets before the player needs them.

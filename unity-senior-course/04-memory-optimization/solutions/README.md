# Solutions 04 — Memory Budget

---

## The fix sequence

A reproducible order of operations that hits < 400 MB on a typical
mobile target.

### Step 1 — Texture import settings

For each enemy texture (and the particle texture):

- **Texture Type**: Default
- **Format**: ASTC 6×6
- **Max Size**: 1024 (or 512 if visual quality allows)
- **Mipmaps**: ☑
- **sRGB**: ☑ (for color textures)

After re-import: 1024×1024 ASTC 6×6 = ~1.3 MB per texture.
30 enemies = ~39 MB. Saving: ~81 MB.

### Step 2 — UI atlas

```
Window → 2D → Sprite Atlas → Create
```

Drag all 50 sprites into the atlas. Set:

- **Format**: ASTC 6×6
- **Max Size**: 2048

Result: ~5.5 MB for the atlas, replacing 50 MB of separate
sprites. Saving: ~44 MB.

### Step 3 — Audio compression

Convert music to Ogg Vorbis at 96 kbps:

```bash
ffmpeg -i music.wav -c:a libvorbis -q:a 4 music.ogg
```

In the import inspector:

- **Load Type**: Streaming (for music) or Compressed In Memory
  (for SFX)
- **Compression Format**: Vorbis
- **Quality**: 0.4 for music, 1.0 for SFX

Result: ~3 MB for the music track. Saving: ~37 MB.

### Step 4 — Pool the bullets

```csharp
public class BulletPool : MonoBehaviour
{
    [SerializeField] Bullet _prefab;
    [SerializeField] int _initialSize = 50;

    readonly Stack<Bullet> _pool = new();

    void Start()
    {
        for (int i = 0; i < _initialSize; i++)
        {
            var b = Instantiate(_prefab, transform);
            b.gameObject.SetActive(false);
            _pool.Push(b);
        }
    }

    public Bullet Get()
    {
        if (_pool.Count == 0) return Instantiate(_prefab, transform);
        var b = _pool.Pop();
        b.gameObject.SetActive(true);
        return b;
    }

    public void Return(Bullet b)
    {
        b.gameObject.SetActive(false);
        _pool.Push(b);
    }
}
```

### Step 5 — Verify with snapshots

Capture before/after snapshots, compute the delta:

```text
Total RSS:         850 → 380 MB
Native → Textures: 220 → 50 MB
Native → Audio:    40 → 3 MB
Managed:           85 → 35 MB
```

The texture import is the biggest win. The atlas is second. Audio
is third. Pooling doesn't reduce RSS significantly but it
**eliminates per-spawn GC allocations** (visible only in the
allocation diff, not in steady-state RSS).

---

## The senior follow-ups

If you have more time, the next steps are:

1. **Addressables for streaming**: load level chunks on demand,
   not at startup. Reduces initial RSS even further.
2. **LODs for distant enemies**: distant enemies use a 256-tri
   mesh instead of 1k-tri. The GPU cost savings are 4× at
   distance.
3. **Mesh compression**: enable `Mesh Compression = Off` →
   `Low/Medium/High` in the import inspector. 50–70% mesh
   memory savings, no visual cost.
4. **Tunable quality**: build a Settings UI that lets the player
   drop to "Low" graphics. On Low: smaller textures, no AA, no
   post FX, fewer particles. The senior games respect the
   player's hardware.

---

## The one-page memory report

A senior PM-readable summary of the audit:

```
Memory Budget Audit — Mobile Target (4-year-old Android)
==========================================================

Baseline:  850 MB RSS
Target:    < 400 MB RSS
Result:    380 MB RSS ✓

Top contributors (post-fix):
  1. Managed code (IL2CPP)        80 MB
  2. URP runtime resources        60 MB
  3. Native engine libs           50 MB
  4. Game textures                50 MB  ← was 220 MB
  5. Audio                        3 MB   ← was 40 MB
  6. Managed heap                 35 MB

Fixes applied:
  - Texture import: ASTC 6×6, max 1024, mipmaps
  - UI: combined into 1 atlas
  - Audio: Ogg Vorbis 96 kbps
  - Bullets: pooled

Open items (not blocking ship):
  - Addressables for non-critical content
  - LOD groups for distant enemies
  - Player-facing quality selector

Build verified on: Pixel 4a, 4 GB RAM, Android 13.
Steady state after 10 min gameplay: 388 MB RSS.
```

This is what a senior ships. Numbers, fixes, what's still open.

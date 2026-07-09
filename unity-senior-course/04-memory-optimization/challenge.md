# Challenge 04 — The Memory Budget

You are the lead of a mobile game that must ship under **512 MB RSS
on a 4-year-old Android phone**. Your team has handed you a memory
audit. Find the problems, fix them, and produce a report that says
the budget is met.

**Time**: 2–3 hours.

---

## The starting state

A small but realistic mobile game scene:

- 1 main camera.
- 1 directional light.
- 30 enemies (each a cube with a 1024×1024 RGBA uncompressed
  texture, **30 × 4 MB = 120 MB**).
- 1 UI canvas with 50 images, each a separate sprite atlas
  (**50 × 1 MB = 50 MB**).
- A 4-minute music track at 44100 Hz stereo 16-bit (**~40 MB**).
- A particle system with 1000 particles, each a 256×256 texture
  (**~1 MB**).
- A `GameManager` script that spawns 5 bullets per second, each
  with a `SpriteRenderer` and no pooling.

**Total estimated RSS** (rough): ~250 MB, not counting engine
overhead. Comfortable on a modern phone, **uncomfortable on the
target device**.

## Your job

Bring the steady-state RSS under **400 MB** while keeping the
gameplay intact. You may:

- Pool the bullets (mandatory).
- Combine the 50 UI sprites into 1 atlas (mandatory).
- Re-encode the music (mandatory).
- Adjust texture import settings (mandatory for the 30 enemies).
- Re-target particle texture (recommended).
- Add a level-of-detail system for distant enemies (stretch).

## Deliverable

A `MemoryBudget/Report.md` with:

1. The starting state: per-category memory (from the Memory
   Profiler Summary).
2. Each fix you applied, with the before/after numbers.
3. The final state, showing < 400 MB total.
4. A "what we'd do with more time" section.

---

## What the senior finds

The fixes that actually move the needle:

### Enemies: 30 × 4 MB = 120 MB

Each enemy has a 1024×1024 RGBA texture. The senior fix:

- Change the texture to ASTC 6×6 (mobile). 1024×1024 ASTC 6×6 is
  ~1.3 MB. **30 × 1.3 = 39 MB**. Saving: **81 MB**.
- If the enemies are visually identical, use a **single shared
  material** with the texture, and GPU instancing (module 7).
- Set `Max Size = 512` if visual quality allows. 512×512 ASTC is
  ~0.4 MB. **30 × 0.4 = 12 MB**. Saving: **108 MB**.

### UI: 50 × 1 MB = 50 MB

50 separate sprite atlases are an editor mistake. Combine them
into one:

- **Window → 2D → Sprite Atlas**.
- Drag all 50 sprites into one atlas.
- Set the atlas to ASTC 6×6.
- Result: one 2048×2048 ASTC atlas (~5.5 MB), and each sprite
  references a region. **Saving: 44 MB**.

### Audio: 40 MB music

- Convert to Vorbis (.ogg) at 96 kbps. A 4-minute track at 96 kbps
  is **~2.9 MB**. **Saving: 37 MB**.
- Lower SFX sample rates to 22050 Hz mono.

### Particles: 1 MB

- 256×256 RGBA → 128×128 ASTC 4×4 is **~0.07 MB**. **Saving:
  ~0.9 MB**.

### Bullets: per-spawn allocations

A `SpriteRenderer` allocation per bullet isn't huge in bytes, but
the GC pressure is the issue. Pool them. (Module 14 covers this
in depth.)

---

## The senior report

```
Memory Budget Report — Mobile Target

Starting state (Memory Profiler Summary):
  Total RSS:        850 MB
  Managed:           85 MB
  Native → Textures: 220 MB
  Native → Audio:    40 MB

After fixes:
  Total RSS:        380 MB
  Managed:           35 MB
  Native → Textures:  50 MB
  Native → Audio:     3 MB

Savings: 470 MB (55% reduction)

Notes:
  - Texture import settings: ASTC 6×6, Max Size 1024.
  - UI: combined into 1 atlas.
  - Audio: Vorbis 96 kbps.
  - Bullets: pooled.

Stretch (not done):
  - Mesh LODs for distant enemies.
  - Streaming levels via Addressables.
  - On-demand loading for non-critical assets.
```

---

## Verify

```bash
# Capture snapshots
unity-capture-snapshot pre.snap
# (apply fixes)
unity-capture-snapshot post.snap

# Diff
unity-compare-snapshots pre.snap post.snap
# expect: massive reduction in Native → Textures
```

If the post-fix is < 400 MB, you pass. If not, find the next
biggest line item and fix it.

---

## What we're testing

- The Memory Profiler Summary is a real engineering tool; you
  can read it and act on it.
- Texture import settings are the dominant mobile-game memory
  lever.
- Audio compression is a 10× memory win for music.
- UI atlasing is mandatory, not optional.
- The senior report is a one-page document with numbers, not
  a paragraph of adjectives.

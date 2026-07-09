# 06 — Rendering: URP, HDRP, SRP Batcher, GPU Instancing

A senior Unity developer **does not write shaders** for the rendering
module's day-to-day. They do, however, understand exactly:

- Why a frame takes 14 ms and how to find the 8 ms cost.
- Why the SRP Batcher is or isn't batching.
- Why a material change in code just doubled the draw calls.
- Why the mobile build has 800 MB of textures and the editor has 200.

This module is the senior rendering toolkit: the **why**, the **tools**,
and the **practical budget numbers** for each platform.

---

## 1. The two render pipelines (and built-in)

| Pipeline | Target | Status |
|----------|--------|--------|
| **Built-in** | Legacy | Deprecated since 2019; not the senior choice |
| **URP (Universal)** | Mobile, mid-range PC, Web | **The right default for 80% of projects** |
| **HDRP (High Definition)** | High-end PC, console | For AAA visuals; mobile is not a target |

**The senior default in 2026**: URP, unless you have an explicit reason
for HDRP. The deprecation of built-in is irreversible. If your project
uses built-in, the right answer is "schedule the migration, not the
ship".

---

## 2. The URP asset: where the budget lives

**Edit → Project Settings → Graphics → URP Global Settings** is the
"render config". Every project needs a URP asset with **renderer
features** configured per platform.

**The senior question**: "What does my URP asset look like on the
lowest-spec target device?" The answer is "lighter".

You can have **multiple URP assets**, one per quality level:

```
Assets/Settings/
  URP-PC-HighQuality.asset
  URP-PC-Medium.asset
  URP-Mobile-Low.asset
```

In **Project Settings → Quality → Rendering**, assign the right URP
asset per quality level. The senior build:

- **PC Ultra**: full HDR, MSAA 4x, all renderer features, post FX on.
- **PC Medium**: HDR off, MSAA 2x, half-res post FX.
- **Mobile High**: HDR off, MSAA 2x, no SSAO, post FX on.
- **Mobile Low**: no HDR, no AA, no SSAO, no post FX.

You ship the right settings per build target.

---

## 3. The three CPU costs in a frame

Every Unity frame (URP, mid-2026) has these CPU costs:

| Cost | What it is | Where you look |
|------|------------|----------------|
| **Player loop / scripts** | Your `Update`s, ECS systems | Profiler → CPU Usage |
| **Rendering setup** | Culling, sorting, draw call recording | Profiler → Rendering |
| **SetPass calls** | Shader-pass changes (state changes) | Profiler → Rendering → **SetPass Calls** count |
| **Draw calls** | Actual `DrawMesh*` to the GPU | Profiler → Rendering |
| **GPU time** | The render passes themselves | Profiler → GPU Usage |

**The senior numbers** (60 FPS target, 16.67 ms):

| Cost | Mobile | PC |
|------|--------|----|
| Scripts | < 4 ms | < 6 ms |
| Rendering setup | < 2 ms | < 3 ms |
| SetPass | < 1 ms | < 1 ms |
| GPU | < 8 ms | < 6 ms |
| Slack | ~1.5 ms | ~0.5 ms |

**SetPass calls are the single CPU number that fixes the most
performance in shipped games.** It is the count of "shader program
switches", and the SRP Batcher is Unity's answer to making it stay
small.

---

## 4. The SRP Batcher: the most underused feature in URP

The SRP Batcher is a path that **combines draw calls that share the
same shader variant** into a single, large draw call, by binding
**per-material** data as a uniform buffer (CBUFFER) instead of
per-object uniforms.

The result: **10,000 cubes with 1 material = 1 SetPass call, not
10,000.**

### The rules for the SRP Batcher to be active

The Frame Debugger (Window → Analysis → Frame Debugger) shows it. In
the right pane for a draw call, you'll see "SRP Batcher: compatible"
or "SRP Batcher: not compatible".

It is **not compatible** if:

- The shader is **not URP-compatible** (built-in shaders, custom
  shaders not migrated to URP).
- The material has **less than 16 properties** that aren't in a
  `CBUFFER`.
- The shader uses **legacy `MaterialPropertyBlock` patterns**
  (more on this below).
- The shader has **multi_compile keywords** that don't fold into
  per-material variants.
- The mesh has **non-uniform scale on the parent** (URP 14+ fixes
  this with `UnityPerMaterial` CBUFFER).

### How to check

In a running scene:

1. **Window → Analysis → Frame Debugger**.
2. Click **Enable**.
3. The first frame's draws appear. Each draw has "SRP Batcher
   compatible" or "incompatible" in the right pane.
4. Sort by "ShaderPassName". Incompatible draws are red.
5. Fix them.

**The single biggest CPU win in most Unity games is fixing SRP
Batcher compatibility.** A 5,000-incompatible draw call game is
3–5× slower than the SRP-batched version, on the same hardware.

---

## 5. GPU Instancing: for the "10,000 of the same mesh" case

For thousands of identical meshes (grass, bullets, particles), GPU
Instancing draws them in **one draw call**, with per-instance
properties fed in as a buffer.

```csharp
using UnityEngine;

public class InstancedGrass : MonoBehaviour
{
    [SerializeField] Mesh _mesh;
    [SerializeField] Material _material;
    [SerializeField] int _count = 10000;
    [SerializeField] float _spread = 50f;

    Matrix4x4[] _matrices;
    void Start()
    {
        _matrices = new Matrix4x4[_count];
        for (int i = 0; i < _count; i++)
        {
            _matrices[i] = Matrix4x4.TRS(
                new Vector3(
                    Random.Range(-_spread, _spread),
                    0f,
                    Random.Range(-_spread, _spread)),
                Quaternion.identity,
                Vector3.one);
        }
    }

    void Update()
    {
        Graphics.DrawMeshInstanced(_mesh, 0, _material, _matrices, _count);
    }
}
```

The material must have **Enable GPU Instancing** ☑ in the inspector.
The shader must be instancing-compatible (URP/Lit is by default).

For per-instance **color or property** variation, use
`MaterialPropertyBlock` with `DrawMeshInstanced`, or use
`Graphics.RenderMeshInstanced` (Unity 2023+) which is the modern API.

**The senior GPU instancing pattern**: use `DrawMeshInstanced` for
static, use `RenderMeshIndirect` (module 7) for "thousands of
individually-moving instances".

---

## 6. LODs: the cheapest 5× you can buy

A **LOD Group** swaps a high-poly mesh for a low-poly one at
distance. The cost saving on the GPU is **enormous**: a 100k-tri
mesh at LOD0 vs a 2k-tri mesh at LOD1 is a **30× vertex count
reduction**.

**Edit in**: GameObject → Add Component → LOD Group.

**The senior LOD rules**:

- 3 LODs is the right default for most games: 0 = full, 1 = half,
  2 = quarter.
- 4 LODs is the right number for open-world: 0 = full, 1 = 0.5,
  2 = 0.25, 3 = billboard or culled.
- LOD bias is the **most fiddled** setting in URP. Test on the
  lowest-spec target; many shipped games ship with LOD bias too
  low and never hit the low-poly LODs.

For DOTS entities, use `LodThreshold` components in a
`LodSelectSystem`.

---

## 7. Texture import: where the budget comes from

**Texture pool size is the dominant memory cost in most Unity
games.** A 1024×1024 uncompressed RGBA32 texture is **4 MB**. A
2048×2048 is **16 MB**. A 4096×4096 is **64 MB**. Multiply by 50
textures and you have a 3 GB game.

The senior import settings:

| Texture type | Compression | Max size | Mipmaps |
|--------------|-------------|----------|---------|
| Diffuse (Albedo) | BC7 (PC) / ASTC 6×6 (mobile) | 2048 (PC), 1024 (mobile) | ☑ |
| Normal map | BC5 (PC) / ASTC 5×5 (mobile) | 1024 (PC), 512 (mobile) | ☑ |
| Roughness / Metal / AO | BC7 / ASTC 6×6 | 1024 (PC), 512 (mobile) | ☑ |
| UI | RGBA32 (no mipmaps) | source size | ☐ |
| Mask | BC4 (PC) / ASTC 4×4 (mobile) | 512 | ☑ |

**The most common senior mistake**: leaving textures as default
(uncompressed, no mipmaps, full res). This is the difference
between a 50 MB build and a 500 MB build.

**Crunch compression** is a special mode that aggressively
shrinks textures at the cost of decode time. Use for non-hot
textures (loading screens, low-frequency background art).

---

## 8. Lighting: the second-biggest GPU cost

**Real-time lighting** is the most expensive thing in a Unity
frame after post FX. The senior rules:

- **Forward+** is the URP default and is correct for most cases.
  Use **Deferred** for many lights.
- **Limit real-time lights per object to 4.** More than that, and
  the shader is recompiled with a different variant. The variant
  count goes up; the build size goes up; the GPU cost goes up.
- **Use lightmaps for everything static.** Lightmaps are a one-time
  bake. Real-time lights are for dynamic things.
- **Use light probes** for moving objects that need to "fit" the
  lightmap.
- **Use reflection probes** for specular reflections; don't rely on
  real-time SSR.
- **No `Add Component → Light → Point` on every projectile.**
  That's a per-frame per-light cost. Use a single directional or
  spot light that follows the player, or use the new
  **RenderObjects** feature in URP.

### The variant explosion

Every real-time light, every shadow caster, every keyword on a
material, **generates a shader variant**. A URP/Lit material with
every feature enabled can have **hundreds of variants**. Each
variant is a few KB. The build is 5–10 MB larger than it should
be, the shader compile time on first frame is 200 ms, and the
PSO cache is too big.

**Use `Shader Variant Collection`** in Player Settings → Graphics
to limit which variants ship.

---

## 9. URP Renderer Features: post FX, render objects, fullscreen

URP's **Renderer Features** are the right place to add custom
rendering: fullscreen blits, RenderObjects, decals, etc. Common
features:

- **Bloom**: cheap, on by default at high quality. Off on mobile low.
- **Tonemapping**: ACES (filmic) for HDR, Neutral for SDR. Pick
  one and stick to it.
- **SSAO**: screen-space ambient occlusion. **Expensive** on
  mobile; off on low.
- **Motion vectors**: needed for TAA / motion blur. **Cheap** if
  you already have them for TAA.
- **TAA (Temporal AA)**: replaces MSAA. Better quality, slightly
  more cost. Senior default for mid/high.
- **SSR (Screen Space Reflections)**: expensive; **off on mobile**.

**The senior post-FX rule**: 2-3 post-FX per platform, not 7. Each
post-FX is a fullscreen pass at your resolution. At 1920×1080, a
fullscreen pass is 2M pixels and bound by fill rate.

---

## 10. MSAA vs TAA: the senior decision

| AA type | Cost | Quality | When |
|---------|------|---------|------|
| **None** | Free | Jagged | Low-end mobile, retro art style |
| **MSAA 2x** | Cheap | OK | Mobile |
| **MSAA 4x** | Mid | Good | PC if you have headroom |
| **TAA** | Cheap-GPU, more memory | Best | Mid/high PC and high mobile |
| **TAA + SMAA** | Slightly more | Best | High-end only |

**TAA is the senior default** for 2026. MSAA is dying because it
doesn't handle specular aliasing and breaks on deferred.

---

## 11. The Profiler: what to look at

In **Window → Analysis → Profiler → Rendering** module:

1. **Total** — should be < 6 ms GPU + < 3 ms render thread.
2. **SetPass Calls** — should be < 200 for a complex scene.
3. **Draw Calls** — should be < 2000.
4. **Triangles** — depends on art budget; ~5M is a normal upper limit.
5. **Vertices** — should be ~2× triangles.
6. **Batches** — should be ≤ SetPass + a few.

**Red flags**:

- SetPass > 1000 → SRP Batcher is breaking. Check the Frame Debugger.
- Batches > DrawCalls × 2 → dynamic batching is failing (don't rely
  on it for static art).
- Triangles > 5M and the camera is looking at one enemy → LODs aren't
  kicking in.

---

## 12. The ProfilerRecorder: a senior's best friend

For long-term tracking (over a level, over a play session), use
`ProfilerRecorder` in code:

```csharp
using Unity.Profiling;

public class FrameStatsLogger : MonoBehaviour
{
    ProfilerRecorder _setPassRecorder;
    ProfilerRecorder _drawCallRecorder;

    void OnEnable()
    {
        _setPassRecorder = ProfilerRecorder.StartNew(
            ProfilerCategory.Render, "SetPass Calls Count");
        _drawCallRecorder = ProfilerRecorder.StartNew(
            ProfilerCategory.Render, "Draw Calls Count");
    }

    void OnDisable()
    {
        _setPassRecorder.Dispose();
        _drawCallRecorder.Dispose();
    }

    void Update()
    {
        Debug.Log($"SetPass: {_setPassRecorder.LastValue}, " +
                  $"DrawCalls: {_drawCallRecorder.LastValue}");
    }
}
```

Use this for automated regression tests, build reports, and over-the-
shoulder reviews.

---

## Summary

- URP is the senior default. HDRP only when you mean it.
- SetPass calls are the single CPU number to fix.
- SRP Batcher: check compatibility in the Frame Debugger. Fix
  incompatibilities before profiling anything else.
- GPU Instancing for thousands of identical meshes.
- LODs for distant detail. Test on the lowest-spec target.
- Texture compression and max size: the 3 GB → 200 MB fix.
- Real-time lights: ≤ 4 per object. Lightmaps for static. Reflection
  probes for specular.
- 2–3 post-FX per platform. Each is a fullscreen pass.
- TAA is the modern senior default.
- ProfilerRecorder for continuous tracking.

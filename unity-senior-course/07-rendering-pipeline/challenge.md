# Challenge 07 — Render 100,000 Cubes at 60 FPS

A studio asks: "can we have 100,000 visible objects in the world
at 60 FPS on a desktop?". The right answer: GPU instancing +
LODs + the senior rendering toolkit.

**Time**: 2-3 hours.

---

## Requirements

- 100,000 cubes visible in a scene.
- 60 FPS on a desktop GPU (e.g. GTX 1060 or better).
- 30 FPS minimum on a 4-year-old mobile GPU.
- LODs at three distances.
- One material, varied color per cube.

## Approach

1. **GPU Instancing**: `Graphics.RenderMeshInstanced` (Unity
   2023+) or `Graphics.DrawMeshInstanced` (legacy). 1 SetPass
   call, 1 Draw call, 100,000 instances.
2. **Per-instance color**: pass a `Vector4[]` of colors via
   `MaterialPropertyBlock.SetVectorArray`.
3. **LODs**: in a custom shader, switch mesh based on view
   distance. Or use multiple `RenderMeshInstanced` calls,
   one per LOD.
4. **Culling**: enable frustum culling. Don't render what
   the camera can't see.
5. **Distance-based LOD**: in the driver script, sort the
   matrices by distance and split them into three arrays
   (one per LOD).

## A senior implementation sketch

```csharp
using UnityEngine;

public class MegaInstancer : MonoBehaviour
{
    [SerializeField] Mesh _meshLod0;
    [SerializeField] Mesh _meshLod1;
    [SerializeField] Mesh _meshLod2;
    [SerializeField] Material _material;
    [SerializeField] int _count = 100_000;
    [SerializeField] float _spread = 200f;

    Matrix4x4[] _matricesLod0, _matricesLod1, _matricesLod2;
    Vector4[] _colors;
    MaterialPropertyBlock _mpb;
    RenderParams _rp;
    Camera _camera;

    void Start()
    {
        _camera = Camera.main;
        var all = new Matrix4x4[_count];
        _colors = new Vector4[_count];
        for (int i = 0; i < _count; i++)
        {
            all[i] = Matrix4x4.TRS(
                new Vector3(
                    Random.Range(-_spread, _spread),
                    Random.Range(-_spread, _spread),
                    Random.Range(-_spread, _spread)),
                Quaternion.identity,
                Vector3.one);
            _colors[i] = new Vector4(
                Random.value, Random.value, Random.value, 1f);
        }

        // Sort by distance to camera; in practice, you can use
        // a simpler heuristic: every Nth instance is a lower LOD.
        _matricesLod0 = Slice(all, 0, 60);
        _matricesLod1 = Slice(all, 60, 90);
        _matricesLod2 = Slice(all, 90, 100);

        _mpb = new MaterialPropertyBlock();
        _mpb.SetVectorArray("_BaseColor", _colors);
        _rp = new RenderParams(_material) { matProps = _mpb };
    }

    static Matrix4x4[] Slice(Matrix4x4[] src, int fromPct, int toPct)
    {
        int from = src.Length * fromPct / 100;
        int to = src.Length * toPct / 100;
        var dst = new Matrix4x4[to - from];
        System.Array.Copy(src, from, dst, 0, dst.Length);
        return dst;
    }

    void Update()
    {
        if (_matricesLod0.Length > 0)
            Graphics.RenderMeshInstanced(_rp, _meshLod0, 0, _matricesLod0);
        if (_matricesLod1.Length > 0)
            Graphics.RenderMeshInstanced(_rp, _meshLod1, 0, _matricesLod1);
        if (_matricesLod2.Length > 0)
            Graphics.RenderMeshInstanced(_rp, _meshLod2, 0, _matricesLod2);
    }
}
```

## Verification

```bash
# Profiler → Rendering
# - SetPass Calls: 1 (or 3 if you have 3 different LODs)
# - Draw Calls: 3 (one per LOD)
# - Visible instances: 100,000
# - GPU frame time: < 8 ms on desktop
```

## Stretch

- **Frustum culling**: in the driver, sort matrices by camera
  distance and only render the ones in the frustum. The
  senior pattern for "millions of instances".
- **GPU-based culling**: use a compute shader to do the LOD
  selection on the GPU. Even faster.
- **Custom shader**: a URP shader with a `_BaseColor` array and
  `INSTANCING_ON` keywords for per-instance variation.
- **Addressables + scene streaming**: load the 100,000 cubes
  from an Addressable subscene; stream them in as the player
  moves.

## What we're testing

- GPU instancing scales to hundreds of thousands.
- LODs are a render-time cost lever, not just a polycount one.
- The senior pipeline is: instanced rendering + LODs + culling.
- Profiler is the verification tool.

The senior dev who can't do this can't ship a strategy game.
